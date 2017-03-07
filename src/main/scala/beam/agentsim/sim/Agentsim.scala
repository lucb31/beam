package beam.agentsim.sim

import java.util.concurrent.TimeUnit

import akka.actor.{ActorRef, ActorSystem, Props}
import akka.pattern.ask
import akka.util.Timeout
import beam.agentsim.agents.PersonAgent
import beam.agentsim.agents.PersonAgent.PersonData
import beam.agentsim.playground.sid.events.EventsSubscriber
import beam.agentsim.playground.sid.events.EventsSubscriber.{FinishProcessing, StartProcessing}
import com.google.inject.Inject
import glokka.Registry
import glokka.Registry.{Created, Found}
import org.matsim.api.core.v01.events.ActivityEndEvent
import org.matsim.api.core.v01.population.Person
import org.matsim.api.core.v01.{Id, Scenario}
import org.matsim.core.api.experimental.events.EventsManager
import org.matsim.core.controler.events.{IterationStartsEvent, ShutdownEvent, StartupEvent}
import org.matsim.core.controler.listener.{IterationStartsListener, ShutdownListener, StartupListener}
import org.matsim.facilities.ActivityFacility

import scala.collection.immutable.ListMap
import scala.concurrent.Await

/**
  * AgentSim entrypoint.
  * Should instantiate the [[ActorSystem]], [[AgentsimServices]] and interact concurrently w/ the QSim.
  *
  * Created by sfeygin on 2/8/17.
  */
class Agentsim @Inject()(private val actorSystem: ActorSystem,
                         private val services: AgentsimServices
                        ) extends StartupListener with IterationStartsListener with ShutdownListener {

  import AgentsimServices._

  val eventsManager: EventsManager = services.matsimServices.getEvents
  val eventSubscriber: ActorRef = actorSystem.actorOf(Props(classOf[EventsSubscriber], eventsManager), "MATSimEventsManagerService")
  val scenario: Scenario = services.matsimServices.getScenario
  val popMap: Map[Id[Person], Person] = ListMap(scala.collection.JavaConverters.mapAsScalaMap(scenario.getPopulation.getPersons).toSeq.sortBy(_._1):_*)

  private implicit val timeout = Timeout(60, TimeUnit.SECONDS)

  override def notifyStartup(event: StartupEvent): Unit = {
    eventSubscriber ! StartProcessing
    // create specific channel for travel events, say
    val actEndDummy = new ActivityEndEvent(0, Id.createPersonId(0), Id.createLinkId(0), Id.create(0, classOf[ActivityFacility]), "dummy")
    agentSimEventsBus.subscribe(eventSubscriber, actEndDummy)
    createAgents()
  }

  override def notifyIterationStarts(event: IterationStartsEvent): Unit = {
    for ((k, _) <- popMap) {
      val future = registry ? Registry.Lookup(k.toString)
      val result = Await.result(future, timeout.duration).asInstanceOf[AnyRef]
      val ok = result.asInstanceOf[Found]
      println(s"${ok.name}")
    }

  }

  override def notifyShutdown(event: ShutdownEvent): Unit = {
    eventSubscriber ! FinishProcessing
    actorSystem.stop(eventSubscriber)
    actorSystem.terminate()

  }

  def createAgents(): Unit = {
    for ((k, v) <- popMap) {
      val props = Props(classOf[PersonAgent], k, PersonData(v.getSelectedPlan))
      val future = registry ? Registry.Register(k.toString, props)
      val result = Await.result(future, timeout.duration).asInstanceOf[AnyRef]
      val ok = result.asInstanceOf[Created]
      println(s"${ok.name}")
    }
  }

}

