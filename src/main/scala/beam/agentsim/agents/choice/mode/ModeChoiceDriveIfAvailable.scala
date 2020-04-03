package beam.agentsim.agents.choice.mode

import beam.agentsim.agents.modalbehaviors.ModeChoiceCalculator
import beam.router.Modes
import beam.router.Modes.BeamMode.CAR
import beam.router.model.EmbodiedBeamTrip
import beam.sim.BeamServices
import beam.sim.config.BeamConfig
import beam.sim.population.AttributesOfIndividual
import org.matsim.api.core.v01.population.{Activity, Person}
import org.matsim.core.utils.misc.Time

import scala.collection.mutable.ListBuffer

/**
  * BEAM
  */
class ModeChoiceDriveIfAvailable(val beamServices: BeamServices) extends ModeChoiceCalculator {

  override lazy val beamConfig: BeamConfig = beamServices.beamConfig

  def apply(
    alternatives: IndexedSeq[EmbodiedBeamTrip],
    attributesOfIndividual: AttributesOfIndividual,
    destinationActivity: Option[Activity],
    person: Option[Person] = None
  ): Option[EmbodiedBeamTrip] = {
    val containsDriveAlt = alternatives.zipWithIndex.collect {
      case (trip, idx) if trip.tripClassifier == CAR => idx
    }
    if (containsDriveAlt.nonEmpty) {
      Some(alternatives(containsDriveAlt.head))
    } else if (alternatives.nonEmpty) {
      Some(alternatives(chooseRandomAlternativeIndex(alternatives)))
    } else {
      None
    }
  }

  override def utilityOf(
    alternative: EmbodiedBeamTrip,
    attributesOfIndividual: AttributesOfIndividual,
    destinationActivity: Option[Activity]
  ): Double = 0.0

  override def utilityOf(mode: Modes.BeamMode, cost: Double, time: Double, numTransfers: Int): Double = 0.0

  override def computeAllDayUtility(
    trips: ListBuffer[EmbodiedBeamTrip],
    person: Person,
    attributesOfIndividual: AttributesOfIndividual
  ): Double = {
    var totalDistanceToDestinationInM: Double = 0.0
    trips.zipWithIndex foreach {case (trip, index) =>
      val tripStartTime = trip.legs.head.beamLeg.startTime
      val drivingLegs = trip.legs.filter(_.beamLeg.mode.value == "car")
      val drivingEndPoint = trip.legs.last.beamLeg.travelPath.endPoint
      val drivingEndPointUtm = this.beamServices.geo.wgs2Utm(drivingEndPoint.loc)
      val destinationActivity = person.getSelectedPlan.getPlanElements.get(index*2 + 2).asInstanceOf[Activity]
      val destinationActivityLocationUtm = destinationActivity.getCoord
      val distanceInM = this.beamServices.geo.distUTMInMeters(destinationActivityLocationUtm, drivingEndPointUtm)
      totalDistanceToDestinationInM += distanceInM
    }
    val walkingDistanceInM = trips.map(
      calculateTripWalkingDistanceInM(_)
    ).sum

    val (endSoc, minSoc) = calculateEndOfDaySOC(trips)
    person.getSelectedPlan.getAttributes.putAttribute("endOfDaySoc", endSoc)
    person.getSelectedPlan.getAttributes.putAttribute("minSoc", minSoc)
    person.getSelectedPlan.getAttributes.putAttribute("walkingDistanceInM", walkingDistanceInM)
    person.getSelectedPlan.getAttributes.putAttribute("totalDistanceToDestinationInM", totalDistanceToDestinationInM)

    val walkingDistanceNormalized = calculateNormalizedWalkingDistance(totalDistanceToDestinationInM, 500, 0.2)
    val minSocRisk = calculateMinSocRisk(minSoc)
    endSoc*beamConfig.ftm.scoring.endSocWeight +
      minSocRisk*beamConfig.ftm.scoring.minSocWeight +
      walkingDistanceNormalized*beamConfig.ftm.scoring.walkingDistanceWeight
  }

  def calculateTripWalkingDistanceInM(trip: EmbodiedBeamTrip): Double = {
    val walkingLegs = trip.legs.filter(_.beamLeg.mode.value == "walk")
    val walkingTripDistanceInM = walkingLegs.map(_.beamLeg.travelPath.distanceInM).sum

    walkingTripDistanceInM
  }

  def calculateEndOfDaySOC (trips: ListBuffer[EmbodiedBeamTrip]) : (Double, Double) = {
    if (trips.size > 0) {
      val filteredLegs = trips.last.legs.filter(_.beamLeg.mode.value == "car")
      if (filteredLegs.size > 0) {
        val vehicleId = filteredLegs.last.beamVehicleId
        val vehicle = this.beamServices.beamScenario.privateVehicles.get(vehicleId).get
        val lastSoc = vehicle.fuelAfterRefuelSession(Time.parseTime(beamServices.beamScenario.beamConfig.beam.agentsim.endTime).toInt) / vehicle.beamVehicleType.primaryFuelCapacityInJoule
        val minSoc = vehicle.minPrimaryFuelLevelInJoules / vehicle.beamVehicleType.primaryFuelCapacityInJoule

        (lastSoc, minSoc)
      }
      else (0, 0)   // Something went wrong

    }
    else {
      // Something went wrong here
      (0, 0)
    }
  }

  def calculateMinSocRisk(minSoc: Double): Double = {
    if (minSoc > 0.8)  1
    else if (minSoc > 0.6) 0.7
    else if (minSoc > 0.3) 0.5
    else if (minSoc > 0.1) 0.2
    else 0
  }

  def calculateNormalizedWalkingDistance(walkingDistance: Double, maxWalkingDistance: Double, residualUtility: Double): Double = {
    val beta = -math.log(residualUtility) / maxWalkingDistance
    math.max(math.exp(-beta*walkingDistance), 0)
  }

}
