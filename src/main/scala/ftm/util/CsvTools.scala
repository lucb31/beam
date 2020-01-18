package ftm.util

import java.io.{FileOutputStream, OutputStreamWriter}

import beam.sim.config.BeamConfig

import scala.reflect.io.{Directory, File}

object CsvTools {
  def writeCsvHeader(headers: String, filePath: String): Unit = {
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

  def writeToCsv(valueSeq: IndexedSeq[Any], fileName: String, config: BeamConfig): Unit = {
    var outputDir = getOutputDirPath(config)
    writeToCsv(valueSeq, outputDir + fileName)
  }

  def getOutputDirPath(config: BeamConfig): String = {
    val baseDir : Directory = File(config.beam.outputs.baseOutputDirectory).toDirectory
    val dirs = baseDir.dirs

    var res = dirs.next().toString()
    while (dirs.hasNext) {
      val currentDir = dirs.next().toString()
      if (currentDir > res) {
        res = currentDir
      }
    }
    res = res + "/"

    res
  }
}
