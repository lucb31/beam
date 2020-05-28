package ftm.run

import java.io.{FileOutputStream, OutputStreamWriter}

import com.typesafe.scalalogging.{LazyLogging}
import ftm.util.{PopulationUtil}
import org.matsim.api.core.v01.{Coord, Id, Scenario}
import org.matsim.api.core.v01.network.{Link, Network}
import org.matsim.api.core.v01.population.{Activity, Leg, Person, Population}
import org.matsim.core.config.ConfigUtils
import org.matsim.core.network.NetworkUtils
import org.matsim.core.network.io.NetworkReaderMatsimV2
import org.matsim.core.population.io.{PopulationReader, PopulationWriter}
import org.matsim.core.router.{FastDijkstraFactory}
import org.matsim.core.router.util.{LeastCostPathCalculator, TravelDisutility, TravelTime}
import org.matsim.core.scenario.ScenarioUtils
import org.matsim.vehicles.{Vehicle, VehicleType}

import scala.language.postfixOps

object GenerateCaseStudyPopulation extends LazyLogging {
  // Configuration
  val plansPath = "/home/lucas/IdeaProjects/beam/test/input/munich-case-study/conversion-input/mito_assignment.50.plans.min.shapefiltered.xml"
  val allPlansPath = "/home/lucas/IdeaProjects/beam/test/input/munich-case-study/conversion-input/mito_assignment.50.plans.min.xml"
  val outputPlansPath = "/home/lucas/IdeaProjects/beam/test/input/munich-case-study/conversion-input/munich-case-study.xml"
  val outputVehiclesCsv = "/home/lucas/IdeaProjects/beam/test/input/munich-case-study/conversion-input/vehicles.csv"
  val networkPath = "test/input/munich-case-study/conversion-input/munich-area-hybrid_generated.xml"
  val sampleSize = 5000
  val days = 3
  val dailyMaxHour = 24
  val workActivityRatio = 0.9
  val smallVehicleRatio = 0.1333
  val mediumVehicleRatio = 0.64
  val bigVehicleRatio = 0.2267
  val vehicleRatios = List(smallVehicleRatio, mediumVehicleRatio, bigVehicleRatio)
  val vehicleNames = List("Smart", "BMW", "Tesla")

  def main(args: Array[String]): Unit = {
    generateVehicles()
    val (population, network) = generatePopulation()
    analysePopulation(population, network)
  }

  def generatePopulation(): (Population, Network) = {

    // Load data
    val config = ConfigUtils.createConfig()
    val scenario: Scenario = ScenarioUtils.loadScenario(config)
    val network: Network = scenario.getNetwork
    val networkReader: NetworkReaderMatsimV2 = new NetworkReaderMatsimV2(network)
    val populationReader = new PopulationReader(scenario)
    //populationReader.readFile(allPlansPath)
    //println("Mito population size is", scenario.getPopulation.getPersons.size())
    populationReader.readFile(plansPath)
    println("Shapefiltered population size is", scenario.getPopulation.getPersons.size())
    networkReader.readFile(networkPath)

    // Sample and repeat plans
    val outputPopulation = PopulationUtil.generateSamplePopulation(sampleSize, scenario.getPopulation, network, workActivityRatio)
    outputPopulation.getPersons.forEach {
      case (_, person: Person) =>
        PopulationUtil.repeatPersonPlan(person.getSelectedPlan, days - 1, dailyMaxHour)
    }

    // Save population to xml
    val populationWriter = new PopulationWriter(outputPopulation)
    populationWriter.write(outputPlansPath)
    (outputPopulation, network)
  }

  def generateVehicles(): Unit = {
    println("Generating vehicles ....")
    var CsvString = "vehicleId,vehicleTypeId"
    var vehicleId = 1
    for (vehicleTypeIndex <- 0 to vehicleRatios.size-1) {
      val ratio = vehicleRatios(vehicleTypeIndex)
      val numberOfVehicles = Math.min(sampleSize - vehicleId, (ratio*sampleSize).asInstanceOf[Int])
      for (i <- 0 to numberOfVehicles) {
        CsvString += "\n" + vehicleId + "," + vehicleNames(vehicleTypeIndex)
        vehicleId += 1
      }
    }
    while(vehicleId < sampleSize) {
      CsvString += "\n" + vehicleId + "," + vehicleNames(vehicleRatios.size - 1)
      vehicleId += 1
    }

    val outputStreamWriter = new OutputStreamWriter(new FileOutputStream(outputVehiclesCsv, false))
    outputStreamWriter.write(CsvString)
    outputStreamWriter.close()
    println("...done")
  }

  def analysePopulation(population: Population, network: Network): Unit = {
    // Initialize routing algorithm
    val costFunction: TravelDisutility = new TravelDisutility {
      override def getLinkTravelDisutility(link: Link, time: Double, person: Person, vehicle: Vehicle): Double = link.getLength

      override def getLinkMinimumTravelDisutility(link: Link): Double = link.getLength
    }
    val travelTime: TravelTime = new TravelTime {
      override def getLinkTravelTime(link: Link, time: Double, person: Person, vehicle: Vehicle): Double = link.getLength / link.getFreespeed
    }
    val dummyVehicle: Vehicle = new Vehicle {
      override def getType: VehicleType = null

      override def getId: Id[Vehicle] = null
    }
    val dijkstraFactory = new FastDijkstraFactory()
    val routingAlg: LeastCostPathCalculator = dijkstraFactory.createPathCalculator(network, costFunction, travelTime)

    var workActs = 0
    var totalActs = 0
    var totalLegs = 0
    var totalTravelDistance = 0.0
    var totalTravelDuration = 0.0
    var numberOfPaths = 0.0
    var totalDailyDistances = 0.0
    var totalDailyDurations = 0.0
    population.getPersons.forEach({
      case (_, person: Person) =>

        var startCoord:  Coord = person.getSelectedPlan.getPlanElements.get(0).asInstanceOf[Activity].getCoord
        var personTravelDistance = 0.0
        var personTravelDuration = 0.0
        var personLegs = 0
        var personActs = 0
        person.getSelectedPlan.getPlanElements.forEach({
          case activity: Activity =>
            personActs += 1
            val endCoord: Coord = activity.getCoord
            val startNode = NetworkUtils.getNearestNode(network, startCoord)
            val endNode = NetworkUtils.getNearestNode(network, endCoord)
            val path = routingAlg.calcLeastCostPath(startNode, endNode, 0.0, person, dummyVehicle)
            personTravelDistance += path.travelCost
            personTravelDuration += path.travelTime
            if (path.travelCost > 0)
              numberOfPaths += 1
            startCoord = endCoord
          case leg: Leg =>
            personLegs += 1
          case _ =>
        })
        totalTravelDistance += personTravelDistance
        totalTravelDuration += personTravelDuration
        totalDailyDistances += personTravelDistance / days
        totalDailyDurations += personTravelDuration / days
        totalLegs += personLegs
        totalActs += personActs
        if (PopulationUtil.checkIfPersonHasWorkAct(person))
          workActs += 1
    })
    println("Sampled total of ", population.getPersons.size(), "plans, ", workActs, "plans with work activities")
    println("Total of " + totalActs + ", average of " + totalActs.asInstanceOf[Double] / population.getPersons.size() + " activities. Total of " + totalLegs + ", average of "+ totalLegs.asInstanceOf[Double] / population.getPersons.size()+"Legs")
    println("Number of paths: "+ numberOfPaths+ ", average Duration per Trip: "+ totalTravelDuration / numberOfPaths + ", averageDistance per Trip" + totalTravelDistance / numberOfPaths )
    println("Average daily distance: " + totalDailyDistances / population.getPersons.size() + ", average daily duration" + totalDailyDurations / population.getPersons.size())
  }
}
