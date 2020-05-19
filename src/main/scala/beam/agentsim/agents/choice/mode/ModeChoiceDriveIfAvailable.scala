package beam.agentsim.agents.choice.mode

import beam.agentsim.agents.modalbehaviors.ModeChoiceCalculator
import beam.router.Modes
import beam.router.Modes.BeamMode.CAR
import beam.router.model.EmbodiedBeamTrip
import beam.sim.BeamServices
import beam.sim.config.BeamConfig
import beam.sim.population.AttributesOfIndividual
import ftm.util.PopulationUtil
import org.matsim.api.core.v01.population.{Activity, Person}
import org.matsim.core.utils.misc.Time

import scala.collection.mutable.{ListBuffer}

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
    // Calculate scoring parameters
    val totalDistanceToDestinationsInM = calcTotalDistanceToDestinationsInM(trips, person)
    val totalWalkingDistanceToDestinationsInM = calcTotalWalkingDistanceToDestinationsInM(trips)
    val (endSoc, minSoc) = calcEndOfIterationSOC(trips)

    // Log scoring parameters
    person.getSelectedPlan.getAttributes.putAttribute("endOfDaySoc", endSoc)
    person.getSelectedPlan.getAttributes.putAttribute("minSoc", minSoc)
    person.getSelectedPlan.getAttributes.putAttribute("walkingDistanceInM", totalWalkingDistanceToDestinationsInM)
    person.getSelectedPlan.getAttributes.putAttribute("totalDistanceToDestinationInM", totalDistanceToDestinationsInM)

    // Normalize scoring parameters
    val walkingDistScore = calcNormalizedWalkingDistance(totalDistanceToDestinationsInM, 500, 0.2)
    val minSocScore = calculateMinSocRiskAcceptance(minSoc)
    val endSocScore = Math.max(0, endSoc)

    // Sum of scoring parameters
    endSocScore*beamConfig.ftm.scoring.endSocWeight +
      minSocScore*beamConfig.ftm.scoring.minSocWeight +
      walkingDistScore*beamConfig.ftm.scoring.walkingDistanceWeight
  }

  def calcTripWalkingDistanceInM(trip: EmbodiedBeamTrip): Double = {
    val walkingLegs = trip.legs.filter(_.beamLeg.mode.value == "walk")
    val walkingTripDistanceInM = walkingLegs.map(_.beamLeg.travelPath.distanceInM).sum

    walkingTripDistanceInM
  }

  def calcTotalWalkingDistanceToDestinationsInM(trips: ListBuffer[EmbodiedBeamTrip]): Double = {
    trips.map(
      calcTripWalkingDistanceInM(_)
    ).sum
  }

  def calcTotalDistanceToDestinationsInM(trips: ListBuffer[EmbodiedBeamTrip], person: Person): Double = {
    var totalDistanceToDestinationInM: Double = 0.0
    trips.zipWithIndex foreach {case (trip, index) =>
      val drivingLegs = trip.legs.filter(_.beamLeg.mode.value == "car")
      var distanceInM: Double = 0.0
      if (drivingLegs.size > 0) {
        val drivingEndpointLinkId = drivingLegs.last.beamLeg.travelPath.linkIds.last
        val drivingEndPoint = drivingLegs.last.beamLeg.travelPath.endPoint
        val drivingEndPointUtm = this.beamServices.geo.wgs2Utm(drivingEndPoint.loc)
        val activities = PopulationUtil.getActivitiesFromPlan(person.getSelectedPlan)
        if (activities.size >= index + 2) {
          val destinationActivity = activities(index + 1)
          // TODO Cleanup
          val destinationActivityLocationLinkId = destinationActivity.getLinkId
          val destinationActivityLocationLink = beamServices.networkHelper.getLink(destinationActivityLocationLinkId.toString.toInt).get
          val drivingEndPointLink = beamServices.networkHelper.getLink(drivingEndpointLinkId.toString.toInt).get
          /*
          val linksConnectByNodeIds =
            destinationActivityLocationLink.getFromNode.getId.toString == drivingEndPointLink.getToNode.getId.toString ||
            destinationActivityLocationLink.getToNode.getId.toString == drivingEndPointLink.getFromNode.getId.toString

           */
          //val id = Id.create(5, classOf[Link])
          val fromConnectByInLinks = destinationActivityLocationLink.getFromNode.getInLinks.containsKey(drivingEndPointLink.getId)
          val fromConnectByOutLinks = destinationActivityLocationLink.getFromNode.getOutLinks.containsKey(drivingEndPointLink.getId)
          val toConnectByInLinks = destinationActivityLocationLink.getToNode.getInLinks.containsKey(drivingEndPointLink.getId)
          val toConnectByOutLinks = destinationActivityLocationLink.getToNode.getOutLinks.containsKey(drivingEndPointLink.getId)
          val linksAreConnected = fromConnectByInLinks || fromConnectByOutLinks || toConnectByInLinks || toConnectByOutLinks
          // Same link is good enough
          if (drivingEndpointLinkId.toString != destinationActivityLocationLinkId.toString && !linksAreConnected) {
            val destinationActivityLocationUtm = destinationActivity.getCoord
            distanceInM = this.beamServices.geo.distUTMInMeters(destinationActivityLocationUtm, drivingEndPointUtm)
          }
        }
      }

      totalDistanceToDestinationInM += distanceInM
    }
    totalDistanceToDestinationInM
  }

  def calcEndOfIterationSOC(trips: ListBuffer[EmbodiedBeamTrip]) : (Double, Double) = {
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

  def calculateMinSocRiskAcceptance(minSoc: Double): Double = {
    if (minSoc > 0.8)  1
    else if (minSoc > 0.6) 0.8
    else if (minSoc > 0.3) 0.6
    else if (minSoc > 0.2) 0.3
    else if (minSoc > 0) 0.2
    else 0
  }

  def calcNormalizedWalkingDistance(walkingDistance: Double, maxWalkingDistance: Double, residualUtility: Double): Double = {
    math.max(math.pow(residualUtility, walkingDistance / maxWalkingDistance), residualUtility)
  }

}
