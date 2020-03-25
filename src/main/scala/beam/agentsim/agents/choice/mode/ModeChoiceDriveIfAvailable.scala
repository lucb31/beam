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
    val walkingDistanceInM = trips.map(
      calculateTripWalkingDistanceInM(_)
    ).sum

    val experiencedPlan = person.getSelectedPlan
    val (endSoc, minSoc) = calculateEndOfDaySOC(trips)
    experiencedPlan.getAttributes.putAttribute("endOfDaySoc", endSoc)
    experiencedPlan.getAttributes.putAttribute("minSoc", minSoc)
    experiencedPlan.getAttributes.putAttribute("walkingDistanceInM", walkingDistanceInM)

    person.asInstanceOf[Person].addPlan(experiencedPlan)
    person.removePlan(person.getSelectedPlan)
    person.asInstanceOf[Person].setSelectedPlan(experiencedPlan)

    walkingDistanceInM
  }

  def calculateTripWalkingDistanceInM(trip: EmbodiedBeamTrip): Double = {
    val walkingLegs = trip.legs.filter(_.beamLeg.mode.value == "walk")
    val walkingTripDistanceInM = walkingLegs.map(_.beamLeg.travelPath.distanceInM).sum

    walkingTripDistanceInM
  }

  def calculateEndOfDaySOC (trips: ListBuffer[EmbodiedBeamTrip]) : (Double, Double) = {
    var lastSoc = 0.0
    var minSoc = 1.0
    trips.foreach { trip =>
      trip.legs.foreach { leg =>
        if (leg.beamLeg.mode.value == "car") {
          val vehicle = this.beamServices.beamScenario.privateVehicles.get(leg.beamVehicleId).get
          val soc = vehicle.primaryFuelLevelInJoules / vehicle.beamVehicleType.primaryFuelCapacityInJoule
          if (soc < minSoc)  minSoc = soc
          lastSoc = vehicle.fuelAfterRefuelSession(Time.parseTime(beamServices.beamScenario.beamConfig.beam.agentsim.endTime).toInt) / vehicle.beamVehicleType.primaryFuelCapacityInJoule
        }
      }
    }

    (lastSoc, minSoc)
  }

}
