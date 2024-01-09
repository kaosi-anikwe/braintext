-- MySQL dump 10.13  Distrib 8.0.35, for Linux (x86_64)
--
-- Host: localhost    Database: braintext
-- ------------------------------------------------------
-- Server version	8.0.35-0ubuntu0.23.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `voice`
--

DROP TABLE IF EXISTS `voice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `voice` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(20) NOT NULL,
  `name` varchar(20) NOT NULL,
  `gender` varchar(20) DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `voice`
--

LOCK TABLES `voice` WRITE;
/*!40000 ALTER TABLE `voice` DISABLE KEYS */;
INSERT INTO `voice` VALUES (1,'en-US-Studio-M','Adam','male','studio','2023-08-24 08:59:37',NULL),(2,'en-US-Wavenet-J','Kevin','male','wavenet','2023-08-24 08:59:37',NULL),(3,'en-US-Wavenet-I','Matthew','male','wavenet','2023-08-24 08:59:37',NULL),(4,'en-US-Neural2-J','William','male','neural','2023-08-24 08:59:37',NULL),(5,'en-US-Neural2-I','David','male','neural','2023-08-24 08:59:37',NULL),(6,'en-US-Neural2-D','Ben','male','neural','2023-08-24 08:59:37',NULL),(7,'en-US-Studio-O','Joanna','female','studio','2023-08-24 08:59:37',NULL),(8,'en-US-Wavenet-H','Ivy','female','wavenet','2023-08-24 08:59:37',NULL),(9,'en-US-Wavenet-F','Isabella','female','wavenet','2023-08-24 08:59:37',NULL),(10,'en-US-Neural2-H','Olivia','female','neural','2023-08-24 08:59:37',NULL),(11,'en-US-Neural2-G','Zoe','female','neural','2023-08-24 08:59:37',NULL),(12,'en-US-Neural2-F','Ava','female','neural','2023-08-24 08:59:37',NULL),(13,'alloy','Michael','male','openai','2023-11-19 06:30:48',NULL),(14,'echo','Benjamin','male','openai','2023-11-19 06:30:48',NULL),(15,'fable','James','male','openai','2023-11-19 06:30:49',NULL),(16,'onyx','Hunter','male','openai','2023-11-19 06:30:49',NULL),(17,'nova','Sophia','female','openai','2023-11-19 06:30:49',NULL),(18,'shimmer','Mia','female','openai','2023-11-19 06:30:49',NULL);
/*!40000 ALTER TABLE `voice` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-12-27  8:26:33
