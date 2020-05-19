package ftm.replanning

import beam.replanning.{PlansStrategyAdopter, ReplanningUtil}
import javax.inject.Inject
import org.matsim.api.core.v01.population._
import org.matsim.core.config.Config
import org.slf4j.LoggerFactory

import scala.util.Random

class RandomizedChargingOrder @Inject()(config: Config) extends PlansStrategyAdopter {
  private val log = LoggerFactory.getLogger(classOf[RandomizedChargingOrder])

  override def run(person: HasPlansAndId[Plan, Person]): Unit = {
    log.debug("Before Replanning RandomizedChargingOrder: Person-" + person.getId + " - " + person.getPlans.size())
    val prevIterationPlanIndex = person.getPlans.indexOf(person.getSelectedPlan)

    // Initialize multiple plans in randomized order
    if (person.getPlans.size() == 1) {
      val random = new Random()
      // Determine number of different combinations by number of activities
      var activities = 0
      person.getSelectedPlan.getPlanElements.forEach {
        case a: Activity => activities += 1
        case l: Leg =>
        case _ =>
      }
      val numberOfCombinations = Math.pow(2, activities-1).toInt

      val chargeAtActivityOrder = random.shuffle(List.range(1, numberOfCombinations))
      chargeAtActivityOrder.foreach(chargeAtActivity => {
        ReplanningUtil.copyPlanAndSelectForMutation(person.getSelectedPlan.getPerson)
        person.getSelectedPlan.getAttributes.clear()
        person.getSelectedPlan.getAttributes.putAttribute("chargeAtActivity", chargeAtActivity)
      })
    }

    // Select next plan in list if available, else start over at first plan
    if (prevIterationPlanIndex < person.getPlans.size() - 1) person.setSelectedPlan(person.getPlans.get(prevIterationPlanIndex + 1))
    else  person.setSelectedPlan(person.getPlans.get(0))

    log.debug("After Replanning RandomizedChargingOrder: Person-" + person.getId + " - " + person.getPlans.size())
  }
}
