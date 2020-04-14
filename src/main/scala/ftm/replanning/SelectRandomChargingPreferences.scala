package ftm.replanning

import beam.replanning.{PlansStrategyAdopter, ReplanningUtil}
import javax.inject.Inject
import org.matsim.api.core.v01.population._
import org.matsim.core.config.Config
import org.slf4j.LoggerFactory

import scala.util.Random

class SelectRandomChargingPreferences @Inject()(config: Config) extends PlansStrategyAdopter {
  private val log = LoggerFactory.getLogger(classOf[SelectRandomChargingPreferences])

  override def run(person: HasPlansAndId[Plan, Person]): Unit = {
    log.debug("Before Replanning SelectRandomChargingPreferences: Person-" + person.getId + " - " + person.getPlans.size())

    // Determine number of different combinations by number of activities
    var activities = 0
    person.getSelectedPlan.getPlanElements.forEach {
      case a: Activity => if (a.getType != "Dummy") activities += 1
      case _ =>
    }
    val numberOfCombinations = Math.pow(2, activities-1).toInt

    // Select random combination of charging preference
    val random = new Random()
    val chargeAtActivity = random.nextInt(numberOfCombinations + 1)
    //ReplanningUtil.makeExperiencedMobSimCompatible(person)
    ReplanningUtil.copyPlanAndSelectForMutation(person.getSelectedPlan.getPerson)
    person.getSelectedPlan.getAttributes.clear()
    person.getSelectedPlan.getAttributes.putAttribute("chargeAtActivity", chargeAtActivity)

    log.debug("After Replanning SelectRandomChargingPreferences: Person-" + person.getId + " - " + person.getPlans.size())
  }
}
