package beam.agentsim.infrastructure.parking

import beam.agentsim.agents.choice.logit.MultinomialLogit

import scala.util.{Failure, Random, Success, Try}
import beam.agentsim.infrastructure.charging._
import beam.agentsim.infrastructure.parking.ParkingRanking.RankingAccumulator
import beam.agentsim.infrastructure.taz.TAZ
import org.matsim.api.core.v01.{Coord, Id}

object ParkingZoneSearch {

  /**
    * a nested structure to support a search over available parking attributes,
    * where traversal either terminates in an un-defined branch (no options found),
    * or a leaf, which contains the index of a ParkingZone in the ParkingZones lookup array
    * with the matching attributes.
    */
  type ZoneSearch = Map[Id[TAZ], Map[ParkingType, List[Int]]]


  /**
    * these are the alternatives that are generated/instantiated by a search
    * and then are selected by either a sampling function (via a multinomial
    * logit function) or by ranking the utility of these alternatives.
    */
  type ParkingAlternative = (TAZ, ParkingType, ParkingZone, Coord)

  /**
    * find the best parking alternative for the data in this request
    * @param destinationUTM coordinates of this request
    * @param valueOfTime agent's value of time in seconds
    * @param chargingInquiry ChargingPreference per type of ChargingPoint
    * @param tazList the TAZ we are looking in
    * @param parkingTypes the parking types we are interested in
    * @param tree search tree of parking infrastructure
    * @param parkingZones stored ParkingZone data
    * @param distanceFunction a function that computes the distance between two coordinates
    * @param random random generator
    * @return the TAZ with the best ParkingZone, it's ParkingType, and the ranking value of that ParkingZone
    */
  def find(
    destinationUTM: Coord,
    valueOfTime: Double,
    parkingDuration: Double,
    chargingInquiry: Option[ChargingInquiry],
    tazList: Seq[TAZ],
    parkingTypes: Seq[ParkingType],
    tree: ZoneSearch,
    parkingZones: Array[ParkingZone],
    distanceFunction: (Coord, Coord) => Double,
    random: Random
  ): Option[RankingAccumulator] = {
    val found = findParkingZones(destinationUTM, tazList, parkingTypes, tree, parkingZones, random)
    takeBestByRanking(destinationUTM, valueOfTime, parkingDuration, found, chargingInquiry, distanceFunction)
  }

  /**
    * look for matching ParkingZones, within a TAZ, which have vacancies
    * @param destinationUTM coordinates of this request
    * @param tazList the TAZ we are looking in
    * @param parkingTypes the parking types we are interested in
    * @param tree search tree of parking infrastructure
    * @param parkingZones stored ParkingZone data
    * @param random random generator
    * @return list of discovered ParkingZones
    */
  def findParkingZones(
    destinationUTM: Coord,
    tazList: Seq[TAZ],
    parkingTypes: Seq[ParkingType],
    tree: ZoneSearch,
    parkingZones: Array[ParkingZone],
    random: Random
  ): Seq[ParkingAlternative] = {

    // conduct search (toList required to combine Option and List monads)
    for {
      taz                 <- tazList
      parkingTypesSubtree <- tree.get(taz.tazId).toList
      parkingType         <- parkingTypes
      parkingZoneIds      <- parkingTypesSubtree.get(parkingType).toList
      parkingZoneId       <- parkingZoneIds
      if parkingZones(parkingZoneId).stallsAvailable > 0
    } yield {
      // get the zone
      Try {
        parkingZones(parkingZoneId)
      } match {
        case Success(parkingZone) =>
          val parkingAvailability: Double = parkingZone.availability
          val stallLocation: Coord =
            ParkingStallSampling.availabilityAwareSampling(random, destinationUTM, taz, parkingAvailability)
          (taz, parkingType, parkingZones(parkingZoneId), stallLocation)
        case Failure(e) =>
          throw new IndexOutOfBoundsException(s"Attempting to access ParkingZone with index $parkingZoneId failed.\n$e")
      }
    }
  }

  // todo JH RJF please talk to JH
  /**
    * samples from the set of discovered stalls using a multinomial logit function
    * @param found the discovered parkingZones
    * @param destinationUTM coordinates of this request
    * @param parkingDuration the duration of the forthcoming agent activity
    * @param valueOfTime this agent's value of time
    * @param utilityFunction a multinomial logit function for sampling utility from a set of parking alternatives
    * @param distanceFunction a function that computes the distance between two coordinates
    * @param random random generator
    * @return the parking alternative that will be used for parking this agent's vehicle
    */
  def takeBestBySampling(
                          found: Iterable[ParkingAlternative],
                          destinationUTM: Coord,
                          parkingDuration: Int,
                          valueOfTime: Double,
                          utilityFunction: MultinomialLogit[ParkingAlternative, String],
                          distanceFunction: (Coord, Coord) => Double,
                          random: Random
                        ): Option[RankingAccumulator] = {

    val alternatives: Iterable[(ParkingAlternative, Map[String, Double])] =
      found.
        map{ parkingAlternative =>

          val (_, _, parkingZone, stallCoordinate) = parkingAlternative

          val parkingTicket: Double = parkingZone.pricingModel match {
            case Some(pricingModel) =>
              PricingModel.evaluateParkingTicket(pricingModel, parkingDuration)
            case None =>
              0.0
          }

          val installedCapacity = parkingZone.chargingPointType match {
            case Some(chargingPoint) => ChargingPointType.getChargingPointInstalledPowerInKw(chargingPoint)
            case None                => 0
          }

          val distance: Double = distanceFunction(destinationUTM, stallCoordinate)

          parkingAlternative ->
            Map(
              "energyPriceFactor" -> (parkingTicket * installedCapacity),
              "distanceFactor"    -> (distance / 1.4 / 3600.0) * valueOfTime,
              "installedCapacity" -> installedCapacity
            )
        }

    // todo: sampleAlternative cannot return None, maybe doesn't need to be returning an Option[], but, what is it's behavior if the input is empty?
    utilityFunction.sampleAlternative(alternatives.toMap, random).
      map{ result =>
        val (taz, parkingType, parkingZone, coordinate) = result.alternativeType

        val utility = result.utility
        RankingAccumulator(
          taz,
          parkingType,
          parkingZone,
          coordinate,
          utility
        )
      }
  }

  /**
    * finds the best parking zone id based on maximizing it's associated cost function evaluation
    * @param destinationUTM coordinates of this request
    * @param found the discovered parkingZones
    * @param chargingInquiry ChargingPreference per type of ChargingPoint
    * @param distanceFunction a function that computes the distance between two coordinates
    * @return the best parking option based on our cost function ranking evaluation
    */
  def takeBestByRanking(
    destinationUTM: Coord,
    valueOfTime: Double,
    parkingDuration: Double,
    found: Iterable[(TAZ, ParkingType, ParkingZone, Coord)],
    chargingInquiry: Option[ChargingInquiry],
    distanceFunction: (Coord, Coord) => Double
  ): Option[RankingAccumulator] = {

    found.foldLeft(Option.empty[RankingAccumulator]) { (accOption, parkingZoneTuple) =>
      val (thisTAZ: TAZ, thisParkingType: ParkingType, thisParkingZone: ParkingZone, stallLocation: Coord) =
        parkingZoneTuple

      val walkingDistance: Double = distanceFunction(destinationUTM, stallLocation)

      // rank this parking zone
      val thisRank = ParkingRanking.rankingValue(
        thisParkingZone,
        parkingDuration,
        walkingDistance,
        valueOfTime,
        chargingInquiry
      )

      // update fold accumulator with best-ranked parking zone along with relevant attributes
      accOption match {
        case None =>
          // the first zone found becomes the first accumulator
          Some {
            RankingAccumulator(
              thisTAZ,
              thisParkingType,
              thisParkingZone,
              stallLocation,
              thisRank
            )
          }
        case Some(acc: RankingAccumulator) =>
          // update the aggregate data, and optionally, update the best zone if it's ranking is superior
          if (acc.bestRankingValue < thisRank) {
            Some {
              acc.copy(
                bestTAZ = thisTAZ,
                bestParkingType = thisParkingType,
                bestParkingZone = thisParkingZone,
                bestCoord = stallLocation,
                bestRankingValue = thisRank
              )
            }
          } else {
            // accumulator has best rank; no change
            accOption
          }
      }
    }
  }
}
