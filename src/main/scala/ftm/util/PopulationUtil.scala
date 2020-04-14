package ftm.util

import beam.replanning.ReplanningUtil
import org.matsim.api.core.v01.population.{Activity, HasPlansAndId, Person, Plan}

import scala.util.Random

object PopulationUtil {
  def copyPlanAndSelectRandomChargingPreference(person: HasPlansAndId[Plan, Person]): Unit = {
    // Determine number of different combinations by number of activities
    val activities = getNumberOfActivities(person.getSelectedPlan)
    val numberOfCombinations = Math.pow(2, activities-1).toInt

    // Select random combination of charging preference
    val random = new Random()
    val chargeAtActivity = random.nextInt(numberOfCombinations + 1)
    //ReplanningUtil.makeExperiencedMobSimCompatible(person)
    ReplanningUtil.copyPlanAndSelectForMutation(person.getSelectedPlan.getPerson)
    person.getSelectedPlan.getAttributes.clear()
    person.getSelectedPlan.getAttributes.putAttribute("chargeAtActivity", chargeAtActivity)
  }

  def getNumberOfActivities(plan: Plan): Int = {
    var activities = 0
    plan.getPlanElements.forEach {
      case a: Activity => if (a.getType != "Dummy") activities += 1
      case _ =>
    }
    activities
  }
  def getChargeAtActivityBooleanSeq(plan: Plan): IndexedSeq[Boolean] = {
    //val combinations = scala.math.pow(2, matsimPlan.getPlanElements.size() - 1).toInt
    val numberOfCombinations = Math.pow(2, getNumberOfActivities(plan)-1).toInt
    val chargeAtActivity = plan.getAttributes.getAttribute("chargeAtActivity").asInstanceOf[Int]
    (0x100 + chargeAtActivity).toBinaryString.tail.map{ case '1' => true; case _ => false }.reverse
  }

  def chargeAtActivityBooleanSeqToString(booleanSeq: IndexedSeq[Boolean]): String = {
    val reverse = booleanSeq.reverse
    var sum = 0.0
    booleanSeq.zipWithIndex.foreach {
      case (value, index) => {
        if (value)
          sum += math.pow(2, index.toInt)
      }
      case _ =>
    }
    sum.toString
  }
}
