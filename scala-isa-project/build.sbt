// The simplest possible sbt build file is just one line:
// For isabelle2023
scalaVersion := "2.13.16"

// For isabelle2022
// scalaVersion := "2.12.17"

// That is, to create a valid sbt build, all you've got to do is define the
// version of Scala you'd like your project to use.

// ============================================================================

// Lines like the above defining `scalaVersion` are called "settings". Settings
// are key/value pairs. In the case of `scalaVersion`, the key is "scalaVersion"
// and the value is "2.13.8"

// It's possible to define many kinds of settings, such as:

name := "scala-isabelle"
organization := "ch.epfl.scala"
version := "1.0"

// Note, it's not required for you to define these three settings. These are
// mostly only necessary if you intend to publish your library's binaries on a
// place like Sonatype.


// Want to use a published library in your project?
// You can define other libraries as dependencies in your build like this:

libraryDependencies += "org.scala-lang.modules" %% "scala-parser-combinators" % "2.3.0"

// Here, `libraryDependencies` is a set of dependencies, and by using `+=`,
// we're adding the scala-parser-combinators dependency to the set of dependencies
// that sbt will go and fetch when it starts up.
// Now, in any Scala file, you can import classes, objects, etc., from
// scala-parser-combinators with a regular import.

// To learn more about multi-project builds, head over to the official sbt
// documentation at http://www.scala-sbt.org/documentation.html

libraryDependencies += "de.unruh" %% "scala-isabelle" % "0.4.3"  // release

libraryDependencies += "org.slf4j" % "slf4j-api" % "2.0.17"
libraryDependencies += "org.apache.logging.log4j" % "log4j-slf4j2-impl" % "2.25.1"


resolvers ++= Resolver.sonatypeOssRepos("snapshots")


assembly / assemblyMergeStrategy := {
  case PathList("org", "slf4j", xs @ _*) => MergeStrategy.first
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x => MergeStrategy.first
}
