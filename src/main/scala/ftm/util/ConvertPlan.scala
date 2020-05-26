package ftm.util

import java.io.{File, FileInputStream, FileOutputStream, OutputStreamWriter}
import java.util.zip.GZIPInputStream

import beam.utils.matsim_conversion.MatsimConversionTool.parseFileSubstitutingInputDirectory
import beam.utils.matsim_conversion.{ConversionConfig, MatsimPlanConversion}
import com.typesafe.scalalogging.StrictLogging
import scala.language.postfixOps

import scala.io.Source

object ConvertPlan extends App with StrictLogging {
  logger.info("Hello")
  if (null != args && args.size > 0) {
    val beamConfigFilePath = args(0) //"test/input/beamville/beam.conf"

    val config = parseFileSubstitutingInputDirectory(beamConfigFilePath)
    convertWithConfig(config)

  } else {
    println("Please specify config/file/path parameter")
  }

  def convertWithConfig(config: com.typesafe.config.Config): Unit = {
    val conversionConfig = ConversionConfig(config)
    MatsimPlanConversion.generateScenarioData(conversionConfig)

    // hacky stuff
    // Copy vehicleTypes
    var src = new File(conversionConfig.scenarioDirectory + "/conversion-input/vehicleTypes.csv")
    var dest = new File(conversionConfig.scenarioDirectory + "/vehicleTypes.csv")
    if (src.isFile())
      new FileOutputStream(dest) getChannel() transferFrom(new FileInputStream(src) getChannel, 0, Long.MaxValue )

    // Copy vehicles
    src = new File(conversionConfig.scenarioDirectory + "/conversion-input/vehicles.csv")
    dest = new File(conversionConfig.scenarioDirectory + "/vehicles.csv")
    if (src.isFile())
      new FileOutputStream(dest) getChannel() transferFrom(new FileInputStream(src) getChannel, 0, Long.MaxValue )


    // Unzip households
    val householdsInput = new File(conversionConfig.scenarioDirectory + "/households.xml.gz")
    val householdsOutput = new File(conversionConfig.scenarioDirectory + "/households.xml")
    val inputStream = new GZIPInputStream(new FileInputStream(householdsInput))
    val outputStreamWriter = new OutputStreamWriter(new FileOutputStream(householdsOutput))
    for (line <- Source.fromInputStream(inputStream).getLines()) {
      outputStreamWriter.write(line+"\n")
    }
    outputStreamWriter.close()
  }
}
