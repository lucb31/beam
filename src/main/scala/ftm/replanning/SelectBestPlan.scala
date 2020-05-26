package ftm.replanning

import beam.replanning.{PlansStrategyAdopter, ReplanningUtil}
import ftm.util.PopulationUtil
import javax.inject.Inject
import org.matsim.api.core.v01.population._
import org.matsim.core.config.Config
import org.slf4j.LoggerFactory

import scala.util.Random

class SelectBestPlan @Inject()(config: Config) extends PlansStrategyAdopter {
  private val log = LoggerFactory.getLogger(classOf[SelectBestPlan])

  override def run(person: HasPlansAndId[Plan, Person]): Unit = {
    log.debug("Before Replanning SelectBestPlan: Person-" + person.getId + " - " + person.getPlans.size())
    /*
    if (person.getPlans.size() < 2) {
      PopulationUtil.copyPlanAndAddRandomChargingActivity(person)
    } else {

     */
    var bestPlan = person.getSelectedPlan
    val iterator = person.getPlans.iterator()
    while (iterator.hasNext) {
      val plan = iterator.next()
      if (plan.getScore > bestPlan.getScore)
        bestPlan = plan
    }
    person.setSelectedPlan(bestPlan)
    //}

    log.debug("After Replanning SelectBestPlan: Person-" + person.getId + " - " + person.getPlans.size())
  }
}
