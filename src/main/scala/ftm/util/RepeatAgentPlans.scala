package ftm.util

import com.typesafe.scalalogging.StrictLogging
import ftm.util.PopulationUtil.getActivitiesFromPlan
import org.matsim.api.core.v01.{Id, Scenario}
import org.matsim.api.core.v01.population.{Activity, Leg, Person}
import org.matsim.core.config.groups.PlansConfigGroup
import org.matsim.core.config.{Config, ConfigUtils}
import org.matsim.core.scenario.ScenarioUtils
import org.matsim.core.population.io.{PopulationReader, PopulationWriter}

import scala.language.postfixOps

object RepeatAgentPlans extends App with StrictLogging {
  logger.info("Hello")
  if (null != args && args.size > 0) {
    val plansPath = args(0) //"test/input/beamville/beam.conf"
    val newPath = args(1)
    val iterations = 2
    val maxHour = 24

    val config = ConfigUtils.createConfig()
    val scenario: Scenario = ScenarioUtils.loadScenario(config)
    val populationReader = new PopulationReader(scenario)
    populationReader.readFile(plansPath)

    scenario.getPopulation.getPersons.forEach {
      case (_, person: Person) =>
        val plan = person.getSelectedPlan
        PopulationUtil.repeatPersonPlan(plan, iterations, maxHour)
    }
    // Dont overwrite files
    if (newPath != plansPath) {
      val populationWriter = new PopulationWriter(scenario.getPopulation)
      populationWriter.write(newPath)
    }
  } else {
    println("Please specify config/file/path parameter")
  }

}
