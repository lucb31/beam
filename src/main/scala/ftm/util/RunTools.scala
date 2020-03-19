package ftm

import beam.sim.config.{BeamConfig, BeamExecutionConfig}
import beam.utils.beam_to_matsim.EventsByVehicleMode.buildViaFile
import beam.utils.beam_to_matsim.events_filter.MutableVehiclesFilter
import ftm.util.{ConvertPlan, CsvTools}

object RunTools {
  def preRunActivity(config: com.typesafe.config.Config, beamExecutionConfig: BeamExecutionConfig): Unit = {
    // TODO Only convert if population file name has changed
    ConvertPlan.convertWithConfig(config)
  }

  def postRunActivity(beamExecutionConfig: BeamExecutionConfig): Unit = {
    val outputDirectory = beamExecutionConfig.outputDirectory
    val lastIter = beamExecutionConfig.beamConfig.beam.agentsim.lastIteration.toString()
    // Convert Events to via readable file
    if (outputDirectory != "") {
      val eventsFile = outputDirectory + "/ITERS/it."+lastIter+"/"+lastIter+".events.csv"
      val outputFile = outputDirectory + "/output_events.xml"
      val selectedModes = "car".split(',').toSeq
      val sampling = 1.0

      Console.println(s"going to transform BEAM events from $eventsFile and write them into $outputFile")
      Console.println(s"selected modes are: ${selectedModes.mkString(",")} and samling is: $sampling")

      val filter = MutableVehiclesFilter.withListOfVehicleModes(selectedModes, sampling)
      buildViaFile(eventsFile, outputFile, filter)
    }
  }
}
