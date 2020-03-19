package ftm.util

import java.io.{FileOutputStream, OutputStreamWriter}

import beam.sim.config.BeamConfig
import beam.utils.FileUtils

import scala.reflect.io.{Directory, File}

object CsvTools {
  def writeCsvHeader(headers: String, filePath: String): Unit = {
    val file : File = File(filePath)
    file.writeAll(headers)
  }

  def writeCsvHeader(headers: String, fileName: String, beamConfig: BeamConfig, currentIteration: Int): Unit = {
    val filePath = getOutputIterDirPath(beamConfig, currentIteration).concat(currentIteration.toString + "." + fileName)
    val file : File = File(filePath)
    file.writeAll(headers)
  }

  def writeToCsv(valueSeq: IndexedSeq[Any], filePath: String): Unit = {
    var CsvString = "\n" + valueSeq(0)
    for (column <- 1 to valueSeq.length - 1) {
      CsvString = CsvString.concat("," + valueSeq(column))
    }

    // TODO maybe check for header
    val outputStreamWriter = new OutputStreamWriter(new FileOutputStream(filePath, true))
    outputStreamWriter.append(CsvString)
    outputStreamWriter.close()
  }

  def writeToCsv(valueSeq: IndexedSeq[Any], fileName: String, beamConfig: BeamConfig): Unit = {
    val outputDir = getOutputDirPath(beamConfig)
    writeToCsv(valueSeq, outputDir + fileName)
  }
  def writeToCsv(valueSeq: IndexedSeq[Any], fileName: String, beamConfig: BeamConfig, currentIteration: Int): Unit = {
    val outputDir = getOutputIterDirPath(beamConfig, currentIteration)
    writeToCsv(valueSeq, outputDir + currentIteration.toString + "." + fileName)
  }

  def getOutputDirPath(beamConfig: BeamConfig): String = {
    FileUtils.getConfigOutputFile(
      beamConfig.beam.outputs.baseOutputDirectory,
      beamConfig.beam.agentsim.simulationName,
      beamConfig.beam.outputs.addTimestampToOutputDirectory).concat("/")
  }

  def getOutputIterDirPath(beamConfig: BeamConfig, currentIteration: Int): String = {
    getOutputDirPath(beamConfig).concat("ITERS/it."+currentIteration.toString+"/")
  }
}
