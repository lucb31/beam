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
    person.getSelectedPlan.getAttributes.removeAttribute("chargeAtActivity")
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
    (numberOfCombinations + chargeAtActivity).toBinaryString.tail.map{ case '1' => true; case _ => false }.reverse
  }

  def chargeAtActivityBooleanSeqToString(booleanSeq: IndexedSeq[Boolean]): Int = {
    var sum = 0.0
    booleanSeq.zipWithIndex.foreach {
      case (value, index) => {
        if (value)
          sum += math.pow(2, index.toInt)
      }
      case _ =>
    }
    sum.toInt
  }

  def addChargingActivityToChargingSequence(sequence: IndexedSeq[Boolean]): IndexedSeq[Boolean] = {
    // Check if we are already charging at every activity
    var newSequence = sequence
    if (sequence.filter(value => value).size < sequence.size) {
      var change = false
      while (!change) {
        val randomIndex = Random.nextInt(sequence.length)
        if (!sequence(randomIndex)) {
          newSequence = sequence.updated(randomIndex, true)
          change = true
        }
      }
    }
    newSequence
  }

  def removeChargingActivityFromChargingSequence(sequence: IndexedSeq[Boolean]): IndexedSeq[Boolean] = {
    // Check if we have a charging activity to remove
    var newSequence = sequence
    if (sequence.filter(value => value).size > 0) {
      var change = false
      while (!change) {
        val randomIndex = Random.nextInt(sequence.length)
        if (sequence(randomIndex)) {
          newSequence = sequence.updated(randomIndex, false)
          change = true
        }
      }
    }
    newSequence
  }

  def moveChargingActivityInChargingSequence(sequence: IndexedSeq[Boolean]): IndexedSeq[Boolean] = {
    // Check if we have a charging activity to move
    var newSequence = sequence
    if (sequence.filter(value => value).size > 0) {
      // make sure the sequence has changed
      while(newSequence == sequence) {
        newSequence = removeChargingActivityFromChargingSequence(newSequence)
        newSequence = addChargingActivityToChargingSequence(newSequence)
      }
    }
    newSequence
  }
}
