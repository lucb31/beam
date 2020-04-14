package ftm.replanning

import beam.replanning.{PlansStrategyAdopter}
import ftm.util.PopulationUtil
import javax.inject.Inject
import org.matsim.api.core.v01.population._
import org.matsim.core.config.Config
import org.slf4j.LoggerFactory


class SelectRandomChargingPreferences @Inject()(config: Config) extends PlansStrategyAdopter {
  private val log = LoggerFactory.getLogger(classOf[SelectRandomChargingPreferences])

  override def run(person: HasPlansAndId[Plan, Person]): Unit = {
    log.debug("Before Replanning SelectRandomChargingPreferences: Person-" + person.getId + " - " + person.getPlans.size())

    PopulationUtil.copyPlanAndSelectRandomChargingPreference(person)

    log.debug("After Replanning SelectRandomChargingPreferences: Person-" + person.getId + " - " + person.getPlans.size())
  }


}
