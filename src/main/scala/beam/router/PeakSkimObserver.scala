package beam.router

import java.util.concurrent.TimeUnit

import akka.actor.{Actor, ActorLogging, Props}
import akka.util.Timeout
import beam.agentsim.agents.BeamAgent.Finish
import beam.agentsim.agents.modalbehaviors.ModeChoiceCalculator
import beam.agentsim.agents.vehicles.VehicleCategory.{Body, Car}
import beam.agentsim.agents.vehicles.VehicleProtocol.StreetVehicle
import beam.agentsim.events.SpaceTime
import beam.router.BeamRouter.{RoutingRequest, RoutingResponse}
import beam.router.Modes.BeamMode.WALK
import beam.router.model.{EmbodiedBeamLeg, EmbodiedBeamTrip}
import beam.sim.BeamServices
import beam.sim.metrics.MetricsSupport
import beam.sim.population.AttributesOfIndividual
import org.matsim.api.core.v01.{Coord, Id}

import scala.concurrent.{ExecutionContext, Future}

class PeakSkimObserver(
  val beamServices: BeamServices,
  val beamSkimmer: BeamSkimmer,
  val modeChoiceCalculator: ModeChoiceCalculator,
  val attributesOfIndividual: AttributesOfIndividual
) extends Actor
    with ActorLogging
    with MetricsSupport {
  private implicit val timeout: Timeout = Timeout(50000, TimeUnit.SECONDS)
  private implicit val executionContext: ExecutionContext = context.dispatcher

  override def receive: PartialFunction[Any, Unit] = {

    case "Run!" =>
      log.info("PeakSkimObserver Begin")
      startSegment("peak-skim-observer", "agentsim")
      val requestTime = (3600.0 * 8.5).intValue()
      val dummyCarVehicleType = beamServices.beamScenario.vehicleTypes.values
        .find(theType => theType.vehicleCategory == Car && theType.maxVelocity.isEmpty)
        .get
      val dummyBodyVehicleType =
        beamServices.beamScenario.vehicleTypes.values.find(theType => theType.vehicleCategory == Body).get
      val tazs = beamServices.beamScenario.tazTreeMap.getTAZs.toList.sortBy(_.tazId.toString)
      val requests = tazs.zipWithIndex.flatten {
        case (originTaz, index) =>
          tazs.slice(0, index + 1).zipWithIndex.map {
            case (destinationTaz, index2) =>
              val dummyStreetVehicle = StreetVehicle(
                Id.createVehicleId("dummy-car-for-skim-observations"),
                dummyCarVehicleType.id,
                new SpaceTime(originTaz.coord, requestTime),
                Modes.BeamMode.CAR,
                asDriver = true
              )
              val originCoord = if (originTaz.tazId.equals(destinationTaz.tazId)) {
                new Coord(originTaz.coord.getX + Math.sqrt(originTaz.areaInSquareMeters) / 4.0, originTaz.coord.getY)
              } else {
                originTaz.coord
              }
              val destCoord = if (originTaz.tazId.equals(destinationTaz.tazId)) {
                new Coord(
                  destinationTaz.coord.getX - Math.sqrt(destinationTaz.areaInSquareMeters) / 4.0,
                  destinationTaz.coord.getY
                )
              } else {
                destinationTaz.coord
              }
              (
                index,
                index2,
                RoutingRequest(
                  originUTM = originCoord,
                  destinationUTM = destCoord,
                  departureTime = requestTime,
                  withTransit = false,
                  streetVehicles = Vector(dummyStreetVehicle)
                )
              )
          }
      }
      Future
        .sequence(
          requests.map {
            case (index, index2, req) =>
              akka.pattern
                .ask(beamServices.beamRouter, req)
                .mapTo[RoutingResponse]
                .map(resp => (index, index2, resp))
          }
        )
        .foreach(_.foreach {
          case (index, index2, response) =>
            val partialTrip = response.itineraries.head.legs
            val theTrip = EmbodiedBeamTrip(
              EmbodiedBeamLeg.dummyLegAt(
                partialTrip.head.beamLeg.startTime,
                Id.createVehicleId("dummy-body"),
                false,
                partialTrip.head.beamLeg.travelPath.startPoint.loc,
                WALK,
                dummyBodyVehicleType.id
              ) +:
              partialTrip :+
              EmbodiedBeamLeg.dummyLegAt(
                partialTrip.last.beamLeg.endTime,
                Id.createVehicleId("dummy-body"),
                true,
                partialTrip.last.beamLeg.travelPath.endPoint.loc,
                WALK,
                dummyBodyVehicleType.id
              )
            )
            val generalizedTime =
              modeChoiceCalculator.getGeneralizedTimeOfTrip(theTrip, Some(attributesOfIndividual), None)
            val generalizedCost = modeChoiceCalculator.getNonTimeCost(theTrip) + attributesOfIndividual
              .getVOT(generalizedTime)
            val energyConsumption = dummyCarVehicleType.primaryFuelConsumptionInJoulePerMeter * theTrip.legs
              .map(_.beamLeg.travelPath.distanceInM)
              .sum
            log.debug(
              s"Observing skim from ${beamServices.beamScenario.tazTreeMap
                .getTAZ(theTrip.legs.head.beamLeg.travelPath.startPoint.loc)
                .tazId} to ${beamServices.beamScenario.tazTreeMap.getTAZ(theTrip.legs.last.beamLeg.travelPath.endPoint.loc).tazId} takes ${generalizedTime} seconds"
            )
            beamSkimmer.observeTrip(theTrip, generalizedTime, generalizedCost, energyConsumption, true)
        })
      endSegment("peak-skim-observer", "agentsim")

    case Finish =>
      context.stop(self)

    case msg @ _ =>
      log.warning(s"Unmatched message received: $msg")
  }

}

object PeakSkimObserver {

  def props(
    beamServices: BeamServices,
    beamSkimmer: BeamSkimmer,
    modeChoiceCalculator: ModeChoiceCalculator,
    attributesOfIndividual: AttributesOfIndividual
  ): Props = {
    Props(
      new PeakSkimObserver(
        beamServices: BeamServices,
        beamSkimmer: BeamSkimmer,
        modeChoiceCalculator: ModeChoiceCalculator,
        attributesOfIndividual: AttributesOfIndividual
      )
    )
  }
}
