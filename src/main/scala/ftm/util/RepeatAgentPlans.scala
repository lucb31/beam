package ftm.util

import com.typesafe.scalalogging.StrictLogging
import ftm.util.PopulationUtil.getActivitiesFromPlan
import org.matsim.api.core.v01.{Id, Scenario}
import org.matsim.api.core.v01.population.{Activity, Leg, Person}
import org.matsim.core.config.groups.PlansConfigGroup
import org.matsim.core.config.{Config, ConfigUtils}
import org.matsim.core.population.PopulationUtils
import org.matsim.core.scenario.ScenarioUtils
import org.matsim.core.population.io.{PopulationReader, PopulationWriter}

import scala.language.postfixOps
import scala.util.Random

object RepeatAgentPlans extends App with StrictLogging {
  logger.info("Hello")
  if (null != args && args.size > 0) {
    val plansPath = args(0) //"test/input/beamville/beam.conf"
    val newPath = args(1)
    val days = 3
    val dailyMaxHour = 24
    val samplePopulationSize = 0

    val config = ConfigUtils.createConfig()
    val scenario: Scenario = ScenarioUtils.loadScenario(config)
    val populationReader = new PopulationReader(scenario)
    populationReader.readFile(plansPath)

    var outputPopulation = PopulationUtils.createPopulation(config)
    if (samplePopulationSize > 0) {
      val random: Random = new Random()
      val personArray = scenario.getPopulation.getPersons.values().toArray()
      val inputPopulationSize = personArray.size
      for (i <- 0 to samplePopulationSize - 1) {
        val nextIndex = random.nextInt(inputPopulationSize)
        val person: Person = personArray(nextIndex).asInstanceOf[Person]

        // Check if unique
        if (!outputPopulation.getPersons.containsValue(person))
          outputPopulation.addPerson(person)
      }
    }
    else
      outputPopulation = scenario.getPopulation

    outputPopulation.getPersons.forEach {
      case (_, person: Person) =>
        PopulationUtil.repeatPersonPlan(person.getSelectedPlan, days - 1, dailyMaxHour)
    }
    // Dont overwrite files
    if (newPath != plansPath) {
      val populationWriter = new PopulationWriter(outputPopulation)
      populationWriter.write(newPath)
    }
  } else {
    println("Please specify config/file/path parameter")
  }

}
