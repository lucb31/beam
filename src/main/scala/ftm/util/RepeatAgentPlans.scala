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
    val plansPath = args(0)
    val newPath = args(1)
    val days = 3
    val dailyMaxHour = 24
    val samplePopulationSize = 3

    val config = ConfigUtils.createConfig()
    val scenario: Scenario = ScenarioUtils.loadScenario(config)
    val populationReader = new PopulationReader(scenario)
    populationReader.readFile(plansPath)
    val outputPopulation = PopulationUtil.generateSamplePopulation(samplePopulationSize, scenario.getPopulation)

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
