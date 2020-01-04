package beam.sim

import beam.utils.beam_to_matsim.EventsByVehicleMode.buildViaFile
import beam.utils.beam_to_matsim.events_filter.MutableVehiclesFilter
import ch.qos.logback.classic.util.ContextInitializer

object RunBeam extends BeamHelper {
  val logbackConfigFile = Option(System.getProperty(ContextInitializer.CONFIG_FILE_PROPERTY))
  if (logbackConfigFile.isEmpty)
    System.setProperty(ContextInitializer.CONFIG_FILE_PROPERTY, "logback.xml")

  def main(args: Array[String]): Unit = {

    print(beamAsciiArt)

    val outputDirectory = runBeamUsing(args)
    logger.info("Exiting BEAM")
    logger.info("Output Directory: " + outputDirectory)

    // Convert Events to via readable file
    if (outputDirectory != "") {
      // TODO select last iteration, not 10th
      val eventsFile = outputDirectory + "/ITERS/it.9/9.events.csv"
      val outputFile = outputDirectory + "/output_events.xml"
      val selectedModes = "car,walk".split(',').toSeq
      val sampling = 1.0

      Console.println(s"going to transform BEAM events from $eventsFile and write them into $outputFile")
      Console.println(s"selected modes are: ${selectedModes.mkString(",")} and samling is: $sampling")

      val filter = MutableVehiclesFilter.withListOfVehicleModes(selectedModes, sampling)
      buildViaFile(eventsFile, outputFile, filter)
    }

    System.exit(0)
  }

}
