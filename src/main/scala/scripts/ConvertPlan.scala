package scripts

import beam.utils.matsim_conversion.{ConversionConfig, MatsimPlanConversion}
import beam.utils.matsim_conversion.MatsimConversionTool.parseFileSubstitutingInputDirectory
import com.typesafe.scalalogging.StrictLogging
import java.io.{File, FileInputStream, FileOutputStream, OutputStreamWriter}
import java.util.zip.{GZIPInputStream, GZIPOutputStream}

import scala.io.Source
import scala.language.postfixOps

object ConvertPlan extends App with StrictLogging {
  logger.info("Hello")
  if (null != args && args.size > 0) {
    val beamConfigFilePath = args(0) //"test/input/beamville/beam.conf"

    val config = parseFileSubstitutingInputDirectory(beamConfigFilePath)
    val conversionConfig = ConversionConfig(config)

    MatsimPlanConversion.generateScenarioData(conversionConfig)

    // hacky stuff
    // Copy vehicleTypes
    val src = new File(conversionConfig.scenarioDirectory + "/conversion-input/vehicleTypes.csv")
    val dest = new File(conversionConfig.scenarioDirectory + "/vehicleTypes.csv")
    new FileOutputStream(dest) getChannel() transferFrom(new FileInputStream(src) getChannel, 0, Long.MaxValue )

    // Unzip households
    val householdsInput = new File(conversionConfig.scenarioDirectory + "/households.xml.gz")
    val householdsOutput = new File(conversionConfig.scenarioDirectory + "/households.xml")
    val inputStream = new GZIPInputStream(new FileInputStream(householdsInput))
    val outputStreamWriter = new OutputStreamWriter(new FileOutputStream(householdsOutput))
    for (line <- Source.fromInputStream(inputStream).getLines()) {
      println(line)
      outputStreamWriter.write(line+"\n")
    }
    outputStreamWriter.close()

  } else {
    println("Please specify config/file/path parameter")
  }
}