-- MySQL dump 10.13  Distrib 8.0.33, for Linux (x86_64)
--
-- Host: localhost    Database: braintext
-- ------------------------------------------------------
-- Server version	8.0.33-0ubuntu0.22.10.2

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
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('daab20f11364');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `basic_subscription`
--

DROP TABLE IF EXISTS `basic_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `basic_subscription` (
  `id` int NOT NULL AUTO_INCREMENT,
  `expire_date` datetime DEFAULT NULL,
  `sub_status` varchar(20) DEFAULT NULL,
  `prompts` int DEFAULT NULL,
  `user_id` int NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `basic_subscription_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `basic_subscription`
--

LOCK TABLES `basic_subscription` WRITE;
/*!40000 ALTER TABLE `basic_subscription` DISABLE KEYS */;
INSERT INTO `basic_subscription` VALUES (1,'2023-05-09 12:45:00','active',3,1,'2023-03-20 16:19:55','2023-05-04 14:10:49'),(2,'2023-03-27 17:10:15','active',0,2,'2023-03-20 17:10:15',NULL),(3,'2023-03-27 17:33:48','active',0,3,'2023-03-20 17:33:48',NULL),(4,'2023-03-27 17:35:47','active',0,4,'2023-03-20 17:35:47',NULL),(5,'2023-04-10 18:06:24','active',3,5,'2023-03-20 18:06:24','2023-04-04 06:11:50'),(6,'2023-04-18 04:06:18','active',3,6,'2023-03-21 04:06:18','2023-04-11 05:32:41'),(7,'2023-04-04 07:20:30','active',1,7,'2023-03-21 07:20:30','2023-04-03 08:51:00'),(8,'2023-04-18 08:41:43','active',3,8,'2023-03-21 08:41:43','2023-04-12 07:28:29'),(9,'2023-04-04 09:00:27','active',3,9,'2023-03-21 09:00:27','2023-03-29 11:49:21'),(10,'2023-04-05 08:37:54','active',3,10,'2023-03-22 08:37:54','2023-03-30 10:35:52'),(11,'2023-04-07 10:17:56','active',3,11,'2023-03-24 10:17:56','2023-04-04 02:44:30'),(12,'2023-05-08 10:01:38','active',3,12,'2023-03-27 10:01:38','2023-05-05 16:56:40'),(13,'2023-05-02 00:16:36','active',3,13,'2023-03-28 00:16:36','2023-04-28 20:58:51'),(15,'2023-04-05 10:58:57','active',0,15,'2023-03-29 10:58:57',NULL),(16,'2023-04-06 20:45:42','active',3,16,'2023-03-30 20:45:42','2023-04-05 06:26:10'),(17,'2023-04-07 23:21:16','active',0,17,'2023-03-31 23:21:16',NULL),(18,'2023-05-06 17:02:55','active',5,18,'2023-04-01 17:02:55','2023-05-01 00:08:19'),(19,'2023-04-10 07:09:11','active',0,19,'2023-04-03 07:09:11',NULL),(20,'2023-04-10 14:47:23','active',3,20,'2023-04-03 14:47:23','2023-04-03 14:56:37'),(21,'2023-04-11 09:23:58','active',0,21,'2023-04-04 09:23:58',NULL),(22,'2023-04-11 10:29:08','active',3,22,'2023-04-04 10:29:08','2023-04-04 10:35:06'),(23,'2023-04-11 21:51:25','active',0,23,'2023-04-04 21:51:25',NULL),(24,'2023-04-12 08:43:54','active',0,24,'2023-04-05 08:43:54',NULL),(25,'2023-04-26 08:49:01','active',3,25,'2023-04-05 08:49:01','2023-04-21 19:58:36'),(26,'2023-04-26 08:51:46','active',3,26,'2023-04-05 08:51:46','2023-04-21 19:52:11'),(27,'2023-05-17 13:31:46','active',7,27,'2023-04-05 13:31:46','2023-05-12 12:31:57'),(28,'2023-04-13 19:04:21','active',3,28,'2023-04-06 19:04:21','2023-04-06 19:10:46'),(29,'2023-04-20 01:00:47','active',0,29,'2023-04-13 01:00:47',NULL),(30,'2023-05-12 14:46:28','active',1,30,'2023-04-14 14:46:28','2023-05-11 13:39:24'),(31,'2023-05-11 10:25:25','active',1,31,'2023-04-20 10:25:25','2023-05-07 09:10:30'),(32,'2023-04-27 15:18:15','active',0,32,'2023-04-20 15:18:15',NULL),(33,'2023-05-25 17:43:16','active',2,33,'2023-04-20 17:43:16','2023-05-19 05:27:05'),(34,'2023-04-28 14:08:37','active',3,34,'2023-04-21 14:08:37','2023-04-21 14:27:44'),(35,'2023-04-29 13:30:40','active',3,35,'2023-04-22 13:30:40','2023-04-22 13:37:30'),(36,'2023-05-04 15:08:06','active',0,36,'2023-04-27 15:08:06',NULL),(37,'2023-05-04 15:14:58','active',3,37,'2023-04-27 15:14:58','2023-04-27 15:22:13'),(38,'2023-05-12 11:16:21','active',10,38,'2023-04-28 11:16:21','2023-05-11 21:32:58'),(39,'2023-05-06 17:20:13','active',1,39,'2023-04-29 17:20:13','2023-05-01 16:23:07'),(40,'2023-05-07 07:35:34','active',3,40,'2023-04-30 07:35:34','2023-04-30 07:46:28'),(41,'2023-05-08 10:36:40','active',3,41,'2023-05-01 10:36:40','2023-05-01 10:38:51'),(42,'2023-05-10 15:42:18','active',4,42,'2023-05-03 15:42:18','2023-05-03 15:54:50'),(43,'2023-05-12 05:04:33','active',2,43,'2023-05-05 05:04:33','2023-05-05 05:27:22'),(44,'2023-05-22 16:31:35','active',3,44,'2023-05-08 16:31:35','2023-05-18 23:41:52'),(45,'2023-05-15 19:21:12','active',2,45,'2023-05-08 19:21:12','2023-05-08 19:25:05'),(46,'2023-05-25 20:16:11','active',1,46,'2023-05-11 20:16:11','2023-05-18 20:38:00'),(47,'2023-05-18 21:04:30','active',5,47,'2023-05-11 21:04:30','2023-05-12 19:34:00'),(48,'2023-05-19 11:46:23','active',10,48,'2023-05-12 11:46:23','2023-05-12 12:56:45'),(49,'2023-05-19 19:39:01','active',3,49,'2023-05-12 19:39:01','2023-05-12 19:43:30'),(50,'2023-05-19 19:41:43','active',0,50,'2023-05-12 19:41:43',NULL),(51,'2023-05-19 19:50:14','active',0,51,'2023-05-12 19:50:14',NULL),(52,'2023-05-20 10:45:18','active',0,52,'2023-05-13 10:45:18',NULL),(53,'2023-05-21 11:20:37','active',1,53,'2023-05-14 11:20:37','2023-05-14 11:22:22'),(54,'2023-05-21 14:45:49','active',0,54,'2023-05-14 14:45:49',NULL),(55,'2023-05-21 14:48:21','active',10,55,'2023-05-14 14:48:21','2023-05-15 18:11:22'),(56,'2023-05-25 11:05:46','active',0,56,'2023-05-18 11:05:46',NULL);
/*!40000 ALTER TABLE `basic_subscription` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `otp`
--

DROP TABLE IF EXISTS `otp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `otp` (
  `id` int NOT NULL AUTO_INCREMENT,
  `phone_no` varchar(20) NOT NULL,
  `otp` int NOT NULL,
  `verified` tinyint(1) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `otp`
--

LOCK TABLES `otp` WRITE;
/*!40000 ALTER TABLE `otp` DISABLE KEYS */;
INSERT INTO `otp` VALUES (1,'+2349016456964',270432,1,'2023-03-20 16:30:20','2023-05-08 17:08:39'),(2,'+2349016456965',556209,0,'2023-03-20 17:09:40','2023-04-02 18:54:55'),(3,'+2349083444922',671635,1,'2023-03-20 18:10:00','2023-03-20 18:10:28'),(4,'+2349032839714',149832,1,'2023-03-21 04:08:32','2023-03-21 04:09:54'),(5,'+2349012658397',569645,1,'2023-03-21 07:26:20','2023-03-21 07:27:14'),(6,'+2349016918868',175811,1,'2023-03-21 08:43:06','2023-04-08 00:40:57'),(7,'+2348067771574',398947,1,'2023-03-21 09:04:54','2023-03-21 09:05:28'),(8,'+2348037272698',498021,1,'2023-03-22 08:43:48','2023-03-22 08:44:13'),(9,'+2348130100510',128631,1,'2023-03-24 10:19:56','2023-03-24 10:20:18'),(10,'+2349093741743',569051,1,'2023-03-27 10:07:17','2023-03-27 10:08:31'),(11,'+2347053571698',693407,1,'2023-03-28 00:21:21','2023-03-28 00:21:42'),(12,'+2349068203687',425697,0,'2023-03-29 11:01:56',NULL),(13,'+2349030847503',468239,1,'2023-03-30 20:48:04','2023-03-30 20:48:40'),(14,'+2348102893682',489642,1,'2023-04-01 17:43:56','2023-04-01 17:44:40'),(15,'+2349164045011',822099,1,'2023-04-03 14:51:37','2023-04-03 14:52:10'),(16,'+2349036839646',793589,1,'2023-04-04 10:31:57','2023-04-04 10:32:20'),(17,'+2348037593827',516909,1,'2023-04-04 10:54:58','2023-04-04 12:00:38'),(18,'+2348088983343',715635,1,'2023-04-04 21:53:16','2023-04-04 21:53:36'),(19,'+2348058947425',530570,1,'2023-04-05 08:53:37','2023-04-05 09:10:56'),(20,'+2349133914609',405125,1,'2023-04-05 08:56:20','2023-04-05 08:56:36'),(21,'+2348080751685',405183,1,'2023-04-06 18:48:55','2023-04-06 18:50:36'),(22,'+2349066732499',336014,1,'2023-04-06 19:07:22','2023-04-06 19:07:49'),(23,'+2348085050841',800645,1,'2023-04-20 10:35:23','2023-04-20 10:35:54'),(24,'+13463818201',740300,1,'2023-04-20 15:19:37','2023-04-20 15:19:52'),(25,'+2347047505886',293105,1,'2023-04-20 17:46:58','2023-04-20 17:47:30'),(26,'+2347048083756',594474,1,'2023-04-21 14:22:02','2023-04-21 14:22:38'),(27,'+2349034376600',800638,1,'2023-04-22 13:33:50','2023-04-22 13:34:15'),(28,'+2349037498252',307593,1,'2023-04-27 15:18:24','2023-04-27 15:18:51'),(29,'+2347031089700',668252,1,'2023-04-28 11:45:29','2023-04-28 11:46:08'),(30,'+2348100394794',372881,1,'2023-04-29 17:32:41','2023-04-29 17:33:16'),(31,'+2349091778708',614720,1,'2023-04-30 07:37:51','2023-04-30 07:38:12'),(32,'+2349131286311',705999,1,'2023-05-01 10:37:30','2023-05-01 10:37:42'),(33,'+2348147270841',599845,1,'2023-05-03 15:43:57','2023-05-03 15:44:28'),(34,'+15512082983',449000,1,'2023-05-05 05:07:42','2023-05-05 05:08:19'),(35,'+2349076811238',378041,1,'2023-05-08 17:10:40','2023-05-08 17:11:02'),(36,'+2348186293740',369699,1,'2023-05-08 19:23:15','2023-05-08 19:23:47'),(37,'+2349078168726',304329,1,'2023-05-11 13:21:16','2023-05-11 13:24:42'),(38,'+2348072860897',194647,1,'2023-05-11 20:22:19','2023-05-11 20:22:53'),(39,'+2349033917463',965879,1,'2023-05-11 21:05:57','2023-05-11 21:06:46'),(40,'+2349060546583',299215,1,'2023-05-12 11:48:11','2023-05-12 11:48:47'),(41,'+2348167555406',819413,1,'2023-05-12 19:41:16','2023-05-12 19:41:29'),(42,'+2348165376040',302513,1,'2023-05-14 11:21:17','2023-05-14 11:22:09'),(43,'+2348143074723',231049,1,'2023-05-14 14:50:40','2023-05-14 14:51:09');
/*!40000 ALTER TABLE `otp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `premium_subscription`
--

DROP TABLE IF EXISTS `premium_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `premium_subscription` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tx_ref` varchar(100) NOT NULL,
  `tx_id` varchar(100) DEFAULT NULL,
  `flw_ref` varchar(100) DEFAULT NULL,
  `payment_status` varchar(20) DEFAULT NULL,
  `sub_status` varchar(20) DEFAULT NULL,
  `expire_date` datetime DEFAULT NULL,
  `user_id` int NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `premium_subscription_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `premium_subscription`
--

LOCK TABLES `premium_subscription` WRITE;
/*!40000 ALTER TABLE `premium_subscription` DISABLE KEYS */;
INSERT INTO `premium_subscription` VALUES (1,'prmum-7fa0251529e843218084e799d9742ed4-1679403897','4215202','FLW-MOCK-1a60fff18ab92c686309afa9ebba4811','completed','expired','2023-03-26 16:55:38',1,'2023-03-21 13:05:01','2023-03-28 10:30:14'),(2,'prmum-b8af84ea235f404db31edff6166e4afa-1679828795','4230789','FLW-MOCK-45791ef5af634bdc0b110edd81a90ce7','completed','expired','2023-04-26 11:08:45',7,'2023-03-26 11:07:07','2023-03-28 10:30:14'),(3,'prmum-7fa0251529e843218084e799d9742ed4-1679915533','4232559','FLW-MOCK-58bbffce7881b2ba10b80f4221926672','completed','expired','2023-03-28 06:05:00',1,'2023-03-27 11:12:21','2023-03-28 10:30:14'),(4,'prmum-7fa0251529e843218084e799d9742ed4-1680004236','4234591','FLW-MOCK-27b76ebe50663b71a8d6ee7dee150ac8','completed','expired','2023-04-28 13:51:38',1,'2023-03-28 11:50:46','2023-04-29 22:24:41'),(5,'prmum-7df5d3a7e021435fa067ebd69cf1d2d2-1680094152',NULL,NULL,'cancelled',NULL,NULL,9,'2023-03-29 12:49:31','2023-03-29 12:51:43'),(6,'prmum-a508e34c1c834179a7e73f560adf7b25-1680204678','4242994','FLW-MOCK-d61b9a6fdaae7bc9c3c3293e30e032fa','completed','expired','2023-04-30 21:33:08',10,'2023-03-30 19:31:30','2023-03-30 20:33:08'),(7,'prmum-7fa0251529e843218084e799d9742ed4-1680478903',NULL,NULL,'cancelled',NULL,'2023-05-03 01:20:19',1,'2023-04-02 23:41:55','2023-04-03 08:09:01'),(8,'prmum-7fa0251529e843218084e799d9742ed4-1680479055','882579488','OAPU3073116804791074','completed','active','2023-06-04 01:55:38',1,'2023-04-02 23:44:23','2023-05-04 06:49:00'),(9,'prmum-0ef4323194c94089a212ace80db9f743-1680534163',NULL,NULL,'pending',NULL,NULL,20,'2023-04-03 15:03:05',NULL),(10,'prmum-7df5d3a7e021435fa067ebd69cf1d2d2-1680550614',NULL,NULL,'cancelled',NULL,NULL,9,'2023-04-03 19:37:45','2023-04-03 19:42:13'),(11,'prmum-7df5d3a7e021435fa067ebd69cf1d2d2-1680550936','883357966','100006230403205122623158486451','completed','active','2023-05-03 20:54:11',9,'2023-04-03 19:42:24','2023-04-03 19:54:11'),(12,'prmum-a508e34c1c834179a7e73f560adf7b25-1680593056','884805447','100006230405124153908550664682','completed','active','2023-05-05 12:44:30',10,'2023-04-04 07:24:28','2023-04-05 11:44:30'),(13,'prmum-e293f0a7301f4a94a21689d69f56efb7-1680609660','883874910','000016230404130422000026238270','completed','active','2023-05-04 13:05:24',21,'2023-04-04 12:01:20','2023-04-04 12:05:26'),(14,'prmum-ed9105049f4a4a91b735c20c5e379065-1680649289','884413997','000016230405000449000029652852','completed','active','2023-05-04 00:15:55',23,'2023-04-04 23:03:15','2023-04-04 23:15:58'),(15,'prmum-b0cd71aeecb04774bec341dd99eb7b7e-1680685173',NULL,NULL,'pending',NULL,NULL,26,'2023-04-05 09:00:00',NULL),(16,'prmum-f30a19f8f4414d57bcf497c1b0b9af00-1680807044','886115452','YIXM2645416808072536','completed','expired','2023-05-06 19:54:48',27,'2023-04-06 18:51:44','2023-05-12 10:31:38'),(17,'prmum-cc2d1d2446894c1cbfe8363fe671fbd4-1680676283',NULL,NULL,'pending',NULL,NULL,16,'2023-04-09 08:49:41',NULL),(18,'prmum-408f3c16055143fc81751f0a949b99a0-1681855063','896533919','BONK7874816818551862','completed','active','2023-05-18 23:00:46',6,'2023-04-18 21:57:54','2023-04-18 22:00:46'),(19,'prmum-2c0f419a2ce440849505d85c0a9a4a56-1682086988',NULL,NULL,'cancelled',NULL,NULL,34,'2023-04-21 14:23:50','2023-04-21 14:25:07'),(20,'prmum-338b28eff0c045299a91215d451a0f0c-1682198935',NULL,NULL,'cancelled',NULL,NULL,8,'2023-04-22 21:29:13','2023-04-22 21:32:28'),(21,'prmum-338b28eff0c045299a91215d451a0f0c-1682199152','900029916','QTDI8797316821991996','completed','active','2023-05-22 22:34:30',8,'2023-04-22 21:32:39','2023-04-22 21:34:30'),(22,'prmum-07b6e8f532ed4580bddd76868a766abc-1682200919',NULL,NULL,'pending',NULL,NULL,32,'2023-04-22 22:03:32',NULL),(23,'prmum-a1354d370bdc4ce5ac1514baa1a3f658-1682608785',NULL,NULL,'pending',NULL,NULL,37,'2023-04-27 15:20:06',NULL),(24,'prmum-2f541bbff9ff43568230709cc99e0569-1683488353','913876829','000016230507213115000091553591','completed','active','2023-06-07 21:33:30',31,'2023-05-07 20:00:59','2023-05-07 20:33:32'),(25,'prmum-7fa0251529e843218084e799d9742ed4-1679403897','4215202','FLW-MOCK-1a60fff18ab92c686309afa9ebba4811','completed','active','2023-05-25 23:49:00',38,'2023-05-17 22:52:14',NULL);
/*!40000 ALTER TABLE `premium_subscription` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `standard_subscription`
--

DROP TABLE IF EXISTS `standard_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `standard_subscription` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tx_ref` varchar(100) NOT NULL,
  `tx_id` varchar(100) DEFAULT NULL,
  `flw_ref` varchar(100) DEFAULT NULL,
  `payment_status` varchar(20) DEFAULT NULL,
  `sub_status` varchar(20) DEFAULT NULL,
  `expire_date` datetime DEFAULT NULL,
  `user_id` int NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `standard_subscription_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `standard_subscription`
--

LOCK TABLES `standard_subscription` WRITE;
/*!40000 ALTER TABLE `standard_subscription` DISABLE KEYS */;
INSERT INTO `standard_subscription` VALUES (1,'stnrd-7fa0251529e843218084e799d9742ed4-1679400288','4215112','FLW-MOCK-248c344dbbb4f9e2a58be53e7a4cc1e1','completed','expired','2023-04-21 12:06:28',1,'2023-03-21 12:04:54','2023-03-28 10:30:14'),(2,'stnrd-7fa0251529e843218084e799d9742ed4-1679915226','4232549','FLW-MOCK-0d5c939167f44f32f34e254f3a17ff76','completed','expired','2023-04-27 11:08:07',1,'2023-03-27 11:07:17','2023-03-28 10:30:14'),(3,'stnrd-8a4bfa6c869941d195d13b0b78a7de9d-1679932900','4232862','FLW-MOCK-256fc16059027f1a2c686efbb9e782a1','completed','expired','2023-04-27 16:03:20',5,'2023-03-27 16:01:48','2023-03-28 10:30:14'),(4,'stnrd-fda86344c016427eb4da39832294a4f5-1679962928',NULL,NULL,'pending',NULL,NULL,13,'2023-03-28 00:22:26',NULL),(5,'stnrd-7fa0251529e843218084e799d9742ed4-1679984202','4233749','FLW-MOCK-be687327e00d20b58a5558e1cfd80ffd','completed','expired','2023-04-28 06:17:27',1,'2023-03-28 06:16:47','2023-03-28 10:30:14'),(6,'stnrd-7fa0251529e843218084e799d9742ed4-1679986009','4233844','FLW-MOCK-0c49ccecd47a38ce3c3d3a43416649e0','completed','expired','2023-03-28 10:48:00',1,'2023-03-28 06:46:52','2023-03-28 10:48:49'),(7,'stnrd-7fa0251529e843218084e799d9742ed4-1680004096','4234586','FLW-MOCK-6e15fee9dcea73e683aa8c7dca1ecd06','completed','upgraded','2023-04-28 13:48:59',1,'2023-03-28 11:48:20','2023-03-28 12:51:38'),(8,'stnrd-e83a95ca496b4db29e1b8b6f7ce9d08c-1680009059',NULL,NULL,'pending',NULL,NULL,12,'2023-03-28 13:11:19',NULL),(9,'stnrd-7fa0251529e843218084e799d9742ed4-1680462560','4247887','FLW-MOCK-4dca1eda0b01d3444eab4aec956de7f8','completed','expired','2023-05-02 21:10:54',1,'2023-04-02 19:09:45','2023-04-02 20:10:54'),(10,'stnrd-7fa0251529e843218084e799d9742ed4-1680468381',NULL,NULL,'cancelled',NULL,NULL,1,'2023-04-02 20:46:42','2023-04-02 20:47:34'),(11,'stnrd-b8af84ea235f404db31edff6166e4afa-1680473482','882860098','100004230403093308103625424303','completed','active','2023-05-03 10:34:13',7,'2023-04-02 22:13:03','2023-04-03 09:34:13'),(12,'stnrd-0ef4323194c94089a212ace80db9f743-1680534163',NULL,NULL,'pending',NULL,NULL,20,'2023-04-03 15:03:32',NULL),(13,'stnrd-b18b81aee1b34d0c81d9d9da81a8ca37-1680605228',NULL,NULL,'pending',NULL,NULL,22,'2023-04-04 10:47:22',NULL),(14,'stnrd-cc2d1d2446894c1cbfe8363fe671fbd4-1680676283',NULL,NULL,'pending',NULL,NULL,16,'2023-04-05 06:31:49',NULL),(15,'stnrd-338b28eff0c045299a91215d451a0f0c-1682198784',NULL,NULL,'cancelled',NULL,NULL,8,'2023-04-22 21:26:39','2023-04-22 21:28:51'),(16,'stnrd-6900b53724394d878d71d5b192839277-1682840297',NULL,NULL,'pending',NULL,NULL,40,'2023-04-30 07:42:34',NULL),(17,'stnrd-2f541bbff9ff43568230709cc99e0569-1683488353',NULL,NULL,'pending',NULL,NULL,31,'2023-05-07 19:53:12',NULL);
/*!40000 ALTER TABLE `standard_subscription` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uid` varchar(200) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `account_type` varchar(20) DEFAULT NULL,
  `phone_no` varchar(20) DEFAULT NULL,
  `phone_verified` tinyint(1) DEFAULT NULL,
  `email_verified` tinyint(1) DEFAULT NULL,
  `edited` tinyint(1) DEFAULT NULL,
  `password_hash` varchar(128) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  `timezone_offset` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'7fa0251529e843218084e799d9742ed4','Kaosi','Anikwe','anikwehenryasa@gmail.com','Premium','+2349016456964',1,1,1,'pbkdf2:sha256:260000$zaI9KemkYVXWsQrZ$cfff7df24712e883e13a87794ee83f3ea786a89cc4c37377ba4a7a71f1c3d43f','2023-03-20 16:19:55','2023-05-08 17:08:39',3600),(2,'9289765736254a12948d8d0c2110f4b0','Kevin','Kevs','anyabuinekevin@gmail.com','Basic',NULL,0,1,0,'pbkdf2:sha256:260000$RUevPFgFZvarY8CG$766dc6278c0c85e2449d7669ed6a75324f217422a6b04491f731ab17326d7202','2023-03-20 17:10:15','2023-03-20 17:13:04',3600),(3,'e47596f68dba4df3a12f13d478fc92d8','Daniel','John','danieljohn@gmail.com','Basic',NULL,0,0,0,'pbkdf2:sha256:260000$z1x0Mk1zuMd2Ys3A$dbf90cd6a96d223437039bb14085c9cad2cf98e09a23fc0db59d0465da977aee','2023-03-20 17:33:48',NULL,3600),(4,'4444004f52734968b16f3aa1770f9abf','Daniel','John','danieljohn2@gmail.com','Basic',NULL,0,0,0,'pbkdf2:sha256:260000$SCzPPYdE3Cxu4lCc$cd1b95d79e2afb4228dc9f1e9875e419c1a019a069c93d03c037546fe1de1f90','2023-03-20 17:35:47',NULL,3600),(5,'8a4bfa6c869941d195d13b0b78a7de9d','Chicheta','Ngene ','ngenechicheta78@gmail.com','Basic','+2349083444922',1,1,0,'pbkdf2:sha256:260000$HbZkUeeIPA6rp8N4$5443e1bcfc4b5ac90cbd9f6967e95a5afd4a73dee05267d00951ad31f4147d4a','2023-03-20 18:06:24','2023-03-27 16:03:20',3600),(6,'408f3c16055143fc81751f0a949b99a0','Peter','ODO','heavenpeter04@gmail.com','Premium','+2349032839714',1,1,0,'pbkdf2:sha256:260000$w48JdoBtxwDGMqHC$0218e656aaccd6b75a7ac36e81f5ed2eb7dd0cbc10a6bd5a08d5d1be836ba71b','2023-03-21 04:06:18','2023-04-18 22:00:46',3600),(7,'b8af84ea235f404db31edff6166e4afa','Tamuno','Bethel','tammybeths400@gmail.com','Standard','+2349012658397',1,1,0,'pbkdf2:sha256:260000$qkz3HXu8WGGAZWQk$2acc877832bd54209af01e154119a22c4a70193285e5dc3e66819f32e3a0ae5a','2023-03-21 07:20:30','2023-04-03 09:34:13',3600),(8,'338b28eff0c045299a91215d451a0f0c','Deborah','Anyachukwu','jesusdebbie01@gmail.com','Premium','+2349016918868',1,1,1,'pbkdf2:sha256:260000$35jfUvuzoPtmWH10$37a9bb9a18c03538ad985a6e0ae20f7ddc837973c03560e23c61c92b217bd599','2023-03-21 08:41:43','2023-04-22 21:34:30',3600),(9,'7df5d3a7e021435fa067ebd69cf1d2d2','Queenesther ','Edeani ','queenestheredeani18@gmail.com','Premium','+2348067771574',1,1,0,'pbkdf2:sha256:260000$y8oPyPZD0sET1U71$60e3eea51f99d079200cd55277a73fb507dc7306e4ca9c6fac58b3a293b7d8cf','2023-03-21 09:00:27','2023-04-03 19:54:11',3600),(10,'a508e34c1c834179a7e73f560adf7b25','Ifeanyi','Anikwe','aianikwe@gmail.com','Premium','+2348037272698',1,1,0,'pbkdf2:sha256:260000$wnfWXYWfTPemZ8d3$c269f2143dfd700661bb078dd48171279c48aa6e04f699b0be0ba5b50cc73215','2023-03-22 08:37:54','2023-04-05 11:44:30',3600),(11,'dc6442a0bd624d90a4a85f4528072641','Sunday','Victor','sundayvictorchinwendu@gmail.com','Basic','+2348130100510',1,1,0,'pbkdf2:sha256:260000$hnNDch5kVa7AEDqU$a010bb8d0e0251d19ff8b445affe6d1fad4450dbd0cd8c3515d28bbb4a77266b','2023-03-24 10:17:56','2023-03-24 10:20:18',3600),(12,'e83a95ca496b4db29e1b8b6f7ce9d08c','Divinesuccess','Ahize','divinesuccessemerem@gmail.com','Basic','+2349093741743',1,1,0,'pbkdf2:sha256:260000$XNsbZgYLts4TnDpp$08e8bd6bd63adcc69393bfc57c0d810f57ffa9b5175e29101bf8c1d32a5f0815','2023-03-27 10:01:38','2023-03-27 10:08:31',3600),(13,'fda86344c016427eb4da39832294a4f5','Eloho','Danielle','danielleeloho85@gmail.com','Basic','+2347053571698',1,1,0,'pbkdf2:sha256:260000$r7TfWp55NzpcOtn7$3858dc636cc19cc479bdbc1b2197524f29f7e22d8f9d7bb284c0950b7f18a032','2023-03-28 00:16:36','2023-03-28 00:21:42',3600),(15,'cbeb0919c61d4aa2a8bc55f75dfc8882','Mmesoma ','Clara','nwogwummesomaclara@gmail.com','Basic',NULL,0,1,0,'pbkdf2:sha256:260000$1VA5GQp4BVLvOpS1$e079992e36ccf60af16d502e759f509e5e2b96916bb75937b36c68bf2264aa6d','2023-03-29 10:58:57','2023-03-29 11:00:25',3600),(16,'cc2d1d2446894c1cbfe8363fe671fbd4','Jenny ','Ezigbo ','joanyezigbo@gmail.com','Basic','+2349030847503',1,1,0,'pbkdf2:sha256:260000$NHq001DrEMWzDsUD$4941ea9f4e4a7987cd95bbce390cfa3e7aa44ca3ed6818e4f40078197dd04c24','2023-03-30 20:45:42','2023-03-30 20:48:40',3600),(17,'5a4ef885de114b9e8a3d0b43eef8bf56','Kaosi','Anikw','anikwhenryasa@gmail.com','Basic',NULL,0,1,0,'pbkdf2:sha256:260000$UPDoZgoq9VldcVLE$a32dac660e553520b3bace82fc2b9c36860856c7c6ad93305a96cc9a890b2927','2023-03-31 23:21:16','2023-04-02 18:34:25',3600),(18,'749b3e1f0a9240eeb9130622ccec69a2','Shealtiel','Asonze','shanzydinero@gmail.com','Basic','+2348102893682',1,1,0,'pbkdf2:sha256:260000$9tb0BLBqvmHccicb$47e81991ca45091f140f631cc88a883ddf29668ea3178f9741024db4a2ecf976','2023-04-01 17:02:55','2023-04-01 17:44:40',3600),(19,'f5bbd3c9dc9b4dae96ee85fc837423a6','Uchegbu','Bright','uchegbubright888@gmail.com','Basic',NULL,0,0,0,'pbkdf2:sha256:260000$RPOZPPNLKYvEIvIq$f10b924870fcc19dc72fa7d22d830a3c4b130d6ef4268bf1deca8035ba99c0c1','2023-04-03 07:09:11',NULL,3600),(20,'0ef4323194c94089a212ace80db9f743','Pascal','Eze','pascaleze001@gmail.com','Basic','+2349164045011',1,1,0,'pbkdf2:sha256:260000$u4P2csdMh5n3V4Nc$9ebd185a884a21407f5b1f4eaaef3f58eebdf6a57181b6c1cd8c91549d5c98c3','2023-04-03 14:47:23','2023-04-03 14:52:10',3600),(21,'e293f0a7301f4a94a21689d69f56efb7','Ogochukwu','Anikwe','ogooanikwe@gmail.com','Premium','+2348037593827',1,1,0,'pbkdf2:sha256:260000$oSGs9C8Z0FtJ16ko$552a67faaba3b099ae55ed3e3fda0bc679251ae730735a5658da4017942ec169','2023-04-04 09:23:58','2023-04-04 12:05:26',3600),(22,'b18b81aee1b34d0c81d9d9da81a8ca37','Chioma','Nnebedum','nnebedumchioma25@gmail.com','Basic','+2349036839646',1,1,0,'pbkdf2:sha256:260000$d7fCNvVkGrfk0L63$942884c611691934ed17c3b0226277e8365f7b3b2da52cfcb99f93b575a9fc69','2023-04-04 10:29:08','2023-04-04 10:32:20',3600),(23,'ed9105049f4a4a91b735c20c5e379065','Nweke','Democritus ','nwekechris90@gmail.com','Premium','+2348088983343',1,1,0,'pbkdf2:sha256:260000$54mO33HQnsKSWYpT$8611735046fa33d669d22ca25fbe626e67d1414a68ed5522b6471560e4dfec17','2023-04-04 21:51:25','2023-04-04 23:15:58',3600),(24,'41edd528734f45028c4fe0138e59de45','Splendour ','Onunwo ','splendouronunwo21@gmail.com','Basic',NULL,0,1,0,'pbkdf2:sha256:260000$OJIY3tEJvuwap4FL$b8582cdd46e2b3f2b3e71b4af6e42c445c8d06b55ca2def9d38558ce776627c7','2023-04-05 08:43:54','2023-04-05 08:46:53',3600),(25,'8c596c56329242e3b7e1cc3f613df773','Tochukwu ','Okoli','okolitochukwu10@gmail.com','Basic','+2348058947425',1,1,0,'pbkdf2:sha256:260000$t6VYCMWxyCRILkRt$66daeb42a9509f74ec797519d75349ffcb299f9fff2e230b891a01d6bc27f2bc','2023-04-05 08:49:01','2023-04-05 09:10:56',3600),(26,'b0cd71aeecb04774bec341dd99eb7b7e','Splendour ','Onunwo ','tokoli829@gmail.com','Basic','+2349133914609',1,1,0,'pbkdf2:sha256:260000$Z4XHyqbwwyX7H1I3$ee398da570d3f78f418b45487a0cedb5b46e9bc6bf3f19b278f07b033de47507','2023-04-05 08:51:46','2023-04-05 08:56:36',3600),(27,'f30a19f8f4414d57bcf497c1b0b9af00','Prince Timothy','Wokoma','princetimo12345@gmail.com','Basic','+2348080751685',1,1,0,'pbkdf2:sha256:260000$8cUbrFf6gwKbNFMy$b1f64a6c13b583a033320cb3ae23c3369d6dca970e9e386102cb549db62886d7','2023-04-05 13:31:46','2023-05-12 10:31:38',3600),(28,'880d645c94e842c4956dcb7a84601837','Raphael','Ugo','codedmesky@gmail.com','Basic','+2349066732499',1,1,0,'pbkdf2:sha256:260000$c177hrsAMi1HwFLo$4a74df36c8d03a5213407730093c5fe9704ccdefd9ee50d94b436dd4331bfb67','2023-04-06 19:04:21','2023-04-06 19:07:49',3600),(29,'e8fce4b826c14ec29efcaec2127b5aa2','Chi','Chi','chinweoke12004@gmail.com','Basic',NULL,0,0,0,'pbkdf2:sha256:260000$b3Qqk02PmbtMMCdj$426ce683627d7421e1f3e40aa43c687b808b18fde59fb9415a136c5b86235c6c','2023-04-13 01:00:47',NULL,3600),(30,'6d2be04cd3474971903dec5aa6b42c92','Tobenna','Chima-uba','tchimauba@gmail.com','Basic','+2349078168726',1,1,0,'pbkdf2:sha256:260000$DNj5DqRca3YB7UY4$f2bc6f08bfd24c063a4d9641469219df2637a32d4827187fae8ee1f2aeab99ec','2023-04-14 14:46:28','2023-05-11 13:24:42',3597),(31,'2f541bbff9ff43568230709cc99e0569','Saviour ','Okereke','saviourokereke52@gmail.com','Premium','+2348085050841',1,1,0,'pbkdf2:sha256:260000$yfl1QmqPdqBNtzm6$cdc2ee85b0c02808b5bec947d28ce9140a6e73b0c79272e634965167e6d49d5b','2023-04-20 10:25:25','2023-05-07 20:33:32',3598),(32,'07b6e8f532ed4580bddd76868a766abc','Ogechukwu','Nwankwo','ogenwankwo2016@gmail.com','Basic','+13463818201',1,1,0,'pbkdf2:sha256:260000$SuCf8SNoaiL4DY8s$22b757060dd8ddf556fccf527931fc00e323533f9d28042f43e9770a41ccd862','2023-04-20 15:18:15','2023-04-20 15:19:52',68399),(33,'d02f0174bafa4ed9885849dc3895a8c7','Beatrice ','Celestine','beatricecelestine22@gmail.com','Basic','+2347047505886',1,1,0,'pbkdf2:sha256:260000$4qi2UrAKzcu6SGmO$46532961e9bf3aabc5da1674b39f9d514497c40fc1a64555b4364a075a20b1f1','2023-04-20 17:43:16','2023-04-20 17:47:30',3596),(34,'2c0f419a2ce440849505d85c0a9a4a56','Aniekan','Israel','aniekaneazy@gmail.com','Basic','+2347048083756',1,1,0,'pbkdf2:sha256:260000$Y0HEHvMokicekabL$492e65a897bb0848905bac87bae49635204be32a2bead322fd134bc7c69abfef','2023-04-21 14:08:37','2023-04-21 14:22:38',3598),(35,'dc6702d9c6c848a1b338c9a3bc607a05','Thomas','Onueze','thomasaquinas742@gmail.com','Basic','+2349034376600',1,1,0,'pbkdf2:sha256:260000$FDcsyFuqkGdMMHam$aacf3fe976877cae2109c7731ae57800411f8da3ad34c8fcebad9ec4938f6e6d','2023-04-22 13:30:40','2023-04-22 13:34:15',3599),(36,'934a797fd5c940dc9af0dd3ff4b9fb65','Benjamin ','Chukwubuiken','justbennybrown@gmail.con','Basic',NULL,0,0,0,'pbkdf2:sha256:260000$YtlRfOmCenf2vo1b$7cfbd6c94f68f74639602ccbf1a8a3ffa41179a4ac4a76a247d9c324f0fb3566','2023-04-27 15:08:06',NULL,3598),(37,'a1354d370bdc4ce5ac1514baa1a3f658','Benjamin','Chukwubuikem','justbennybrown@gmail.com','Basic','+2349037498252',1,1,0,'pbkdf2:sha256:260000$C9duk4ixGiBzcGpR$995d1ee11f78975a6df0ded8e9f775d782b463a9c42d178e06377fff8d89f72b','2023-04-27 15:14:58','2023-04-27 15:18:51',3580),(38,'88e4919b10b34ee1b57fe22384483a28','Nwokeke ','Augustine ','cruzmegadron@gmail.com','Premium','+2347031089700',1,1,0,'pbkdf2:sha256:260000$K2h53eDDWBHmPndg$b22df385d0c2d72b4c903cf1983fc5bac1f683366ba15295d5ed56a096373ef5','2023-04-28 11:16:21','2023-04-28 11:46:08',3595),(39,'5fdad540d4564218bd465f31401de88f','Nkwocha ','Olivianna','oliviannankwocha48@gmail.com','Basic','+2348100394794',1,1,0,'pbkdf2:sha256:260000$RnMkksMID18D533g$aa991d41d1e60006a0fc69b101b242e212e6fdadafbad7c4ef79f29edee0ef6f','2023-04-29 17:20:13','2023-04-29 17:33:16',3598),(40,'6900b53724394d878d71d5b192839277','Eze','Miracle','ezemiracle13@gmail.com','Basic','+2349091778708',1,1,0,'pbkdf2:sha256:260000$JXbstxZwOV5qCNTe$50b1286352f46454872f37fb750275ae869f7b78a097ac343f0cba7004a53aab','2023-04-30 07:35:34','2023-04-30 07:38:12',3597),(41,'7bb0b7621bc14eddbb19e3d5f9e10de1','Bolajii','Chibuzor-Orie','godswillchibuzororie@gmail.com','Basic','+2349131286311',1,1,0,'pbkdf2:sha256:260000$oR7a2VOEq7CxSv8S$ae4439dde984b5e24bb6afd5945657d8396be74fac80c22de1ca0366e20547af','2023-05-01 10:36:40','2023-05-01 10:37:42',3599),(42,'e9e2ad13e0c94e36ab1ca5088cce3a84','Izuchukwu','Uchendu ','izuchukwu.uchendu@gmail.com','Basic','+2348147270841',1,1,0,'pbkdf2:sha256:260000$6k5mKGH87Ryiwkya$9887e8b8e1e32cbb6017ee6c15b528b3c282b804f7a3049e1a9568682d59d549','2023-05-03 15:42:18','2023-05-03 15:44:28',3597),(43,'04f0181045424ca78351d933683776a8','Ujunwa','Okeke','ujunwauxbootcamp@gmail.com','Basic','+15512082983',1,1,0,'pbkdf2:sha256:260000$NRIDMx6z1FgvKIbW$1d16d6ca1b57a83d07a7d69f6efc4b877eeda92c0286398ad2570dc4acf03765','2023-05-05 05:04:33','2023-05-05 05:08:19',61200),(44,'d369a0ab175e4a4e9c876dd0092f98fb','Chiamaka','Chime','Chiamakarules@gmail.com','Basic','+2349076811238',1,1,0,'pbkdf2:sha256:260000$n6EaHqzFYVEIIcVU$f9142e9f47f47b2705eeae0bef52f78f4823c0f8d185f3549b2b026668ce2812','2023-05-08 16:31:35','2023-05-08 17:11:02',3600),(45,'0b45dec77b0646d298d3eaa1e7b255f3','Osita','OKEKE','osii76@yahoo.co.uk','Basic','+2348186293740',1,1,0,'pbkdf2:sha256:260000$PuBTfZ49mhV8jKGB$a57dffa5082516d010db71c90c6cfa9b3962cf8b12ce14a16bf5ca0545d4a45d','2023-05-08 19:21:12','2023-05-08 19:23:47',3600),(46,'ddb9b8b2ae81463f8b29e48113e4f318','Yvette','Cheery','azubikeyvette@gmail.com','Basic','+2348072860897',1,1,0,'pbkdf2:sha256:260000$2lXNZ3k5EZQIj8kz$a55460d3f3ddb532d53740aa5bb1f16bf96c3fa61c843e850e09b715412a5169','2023-05-11 20:16:11','2023-05-11 20:22:53',3600),(47,'1c97b805ddc644d4b491f74078e1d999','Elvis ','Dennis ','Dennisstanislaus4@gmail.com','Basic','+2349033917463',1,1,0,'pbkdf2:sha256:260000$QkEQ7DfN73QKRkra$38cdbad700d48cf9f40ad50f27ae0455508d0410f459d0203d7a03e5698dd04d','2023-05-11 21:04:30','2023-05-11 21:06:46',3600),(48,'6a79f3d2ea6e4a0c88c40ad51ab2a8c7','Raphael ','Chibuike ','raphaelchibuike7251@gmail.com','Basic','+2349060546583',1,1,0,'pbkdf2:sha256:260000$RubfyW4EtEpg1JH4$b896e3038a54b856d7aeb9a4216559a761b4f3bff077dabeca8e49ec491656b9','2023-05-12 11:46:23','2023-05-12 11:48:47',3600),(49,'9a94da32a0cc47d880d3af0c895df5a7','Elochukwu','Nwaduche','emmanuelnwaduche@gmail.com','Basic','+2348167555406',1,1,0,'pbkdf2:sha256:260000$ciYHhZRDlolaOHSg$f0fe28a7055320378603298f0e490f11d811c8f948daccd60e694bd6d498a483','2023-05-12 19:39:00','2023-05-12 19:41:29',3600),(50,'d92fe033671e4561801af285923ebaad','Jacinta','Oluchi','sundayjacinta8@gmail.com','Basic',NULL,0,1,0,'pbkdf2:sha256:260000$zfTkl49zRnV07P86$6e4311cb2315fd4bedd59f7e685be9b42e96eaa7e47661f7bf59a10799c17ea5','2023-05-12 19:41:43','2023-05-12 19:52:58',3600),(51,'b7f2561939d64324a36fcd58e214223b','Jacinta','Oluchi','jaceejacee26@gmail.com','Basic',NULL,0,0,0,'pbkdf2:sha256:260000$9aIFWYedPoH2dCG8$8d207e0ad26f938132187c735994795d0539cbe3defcfecec2acd4b85e718ed8','2023-05-12 19:50:13',NULL,3600),(52,'b812acd6707f4bfdbd25645bafb575fd','Isaac','Kingsley ','isaackingsleyfortunate@gmail.com','Basic',NULL,0,1,0,'pbkdf2:sha256:260000$d4HQ7GBH7U9J2Xax$26337a1e36a4421cb4da9fdd09d27ca6a304899cb5c837c2ecd4a7278b2bcc78','2023-05-13 10:45:18','2023-05-13 11:14:07',3600),(53,'00b4b3d80d6d4d8a994e5ad2496da500','Princewill','Ubong','kfasrb@gmail.com','Basic','+2348165376040',1,1,0,'pbkdf2:sha256:260000$Ctty213tw6sn5Ehi$b668e57f1e42f4d1b09d82613e6207e8f4248cad30ce670265ad8a1a7cd50728','2023-05-14 11:20:37','2023-05-14 11:22:09',3600),(54,'7753415ac33a418fbfb7d0f82e575c6b','Great','Darego','greatdarego@gmail.com','Basic',NULL,0,0,0,'pbkdf2:sha256:260000$a0b1XF0U6InJzidQ$2031318ef43b114985f086549bde35ec2395a32ec7d862c98c02dc04382f949e','2023-05-14 14:45:49',NULL,3600),(55,'7a6fa2e9b53f46c4992abc46a7b55aa6','THANK-GOD ','UCHENDU ','apexthankgod@gmail.com','Basic','+2348143074723',1,1,0,'pbkdf2:sha256:260000$4MvexNYm9Z1KM8N1$41c662a0318b227f46b72497f0c4e4dfa2700530b051d83fbef2161671c7f571','2023-05-14 14:48:21','2023-05-14 14:51:09',3600),(56,'89016b760e4c4bee80d6dd25fd482900','Chibuisi ','Robert ','robertconfy18@gmail.com','Basic',NULL,0,1,0,'pbkdf2:sha256:260000$PYCabQwm0nwnF4Jp$a4967dbd8f8496c098972c1ce4fd24ba89cd601cd459f1edfa6efcef0af0b1be','2023-05-18 11:05:46','2023-05-18 11:10:50',3600);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_setting`
--

DROP TABLE IF EXISTS `user_setting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_setting` (
  `id` int NOT NULL AUTO_INCREMENT,
  `notify_on_profile_change` tinyint(1) DEFAULT NULL,
  `product_updates` tinyint(1) DEFAULT NULL,
  `subscription_expiry` tinyint(1) DEFAULT NULL,
  `ai_voice_type` varchar(50) DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  `voice_response` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_setting_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_setting`
--

LOCK TABLES `user_setting` WRITE;
/*!40000 ALTER TABLE `user_setting` DISABLE KEYS */;
INSERT INTO `user_setting` VALUES (1,0,0,1,'Joey',1,'2023-03-20 16:19:55','2023-04-29 22:24:53',1),(2,0,0,1,'Joanna',2,'2023-03-20 17:10:15',NULL,1),(3,0,0,1,'Joanna',3,'2023-03-20 17:33:48',NULL,1),(4,0,0,1,'Joanna',4,'2023-03-20 17:35:47',NULL,1),(5,0,0,1,'Joanna',5,'2023-03-20 18:06:24',NULL,1),(6,0,0,1,'Joanna',6,'2023-03-21 04:06:18',NULL,1),(7,0,0,1,'Ivy',7,'2023-03-21 07:20:30','2023-03-26 14:34:17',1),(8,0,0,1,'Joanna',8,'2023-03-21 08:41:43',NULL,1),(9,0,0,1,'Joanna',9,'2023-03-21 09:00:27',NULL,1),(10,0,0,1,'Joanna',10,'2023-03-22 08:37:54',NULL,1),(11,0,0,1,'Joanna',11,'2023-03-24 10:17:56',NULL,1),(12,0,0,1,'Joanna',12,'2023-03-27 10:01:38',NULL,1),(13,0,0,1,'Joanna',13,'2023-03-28 00:16:36',NULL,1),(15,0,0,1,'Joanna',15,'2023-03-29 10:58:57',NULL,1),(16,0,0,1,'Joanna',16,'2023-03-30 20:45:42',NULL,1),(17,0,0,1,'Joanna',17,'2023-03-31 23:21:16',NULL,1),(18,0,0,1,'Joanna',18,'2023-04-01 17:02:55',NULL,1),(19,0,0,1,'Joanna',19,'2023-04-03 07:09:11',NULL,1),(20,0,0,1,'Joanna',20,'2023-04-03 14:47:23',NULL,1),(21,0,0,1,'Joanna',21,'2023-04-04 09:23:58',NULL,1),(22,0,0,1,'Joanna',22,'2023-04-04 10:29:08',NULL,1),(23,0,0,1,'Joanna',23,'2023-04-04 21:51:25',NULL,1),(24,0,0,1,'Joanna',24,'2023-04-05 08:43:54',NULL,1),(25,0,0,1,'Joanna',25,'2023-04-05 08:49:01',NULL,1),(26,0,0,1,'Joanna',26,'2023-04-05 08:51:46',NULL,1),(27,0,0,1,'Joanna',27,'2023-04-05 13:31:46',NULL,1),(28,0,0,1,'Joanna',28,'2023-04-06 19:04:22',NULL,1),(29,0,0,1,'Joanna',29,'2023-04-13 01:00:48',NULL,1),(30,0,0,1,'Joanna',30,'2023-04-14 14:46:28',NULL,1),(31,0,0,1,'Joanna',31,'2023-04-20 10:25:25',NULL,1),(32,0,0,1,'Joanna',32,'2023-04-20 15:18:15',NULL,1),(33,0,0,1,'Joanna',33,'2023-04-20 17:43:16',NULL,1),(34,0,0,1,'Joanna',34,'2023-04-21 14:08:37',NULL,1),(35,0,0,1,'Joanna',35,'2023-04-22 13:30:40',NULL,1),(36,0,0,1,'Joanna',36,'2023-04-27 15:08:06',NULL,1),(37,0,0,1,'Joanna',37,'2023-04-27 15:14:58',NULL,1),(38,0,0,1,'Joanna',38,'2023-04-28 11:16:21',NULL,1),(39,0,0,1,'Joanna',39,'2023-04-29 17:20:13',NULL,1),(40,0,0,1,'Joanna',40,'2023-04-30 07:35:34',NULL,1),(41,0,0,1,'Joanna',41,'2023-05-01 10:36:40',NULL,1),(42,0,0,1,'Joanna',42,'2023-05-03 15:42:18',NULL,1),(43,0,0,1,'Joanna',43,'2023-05-05 05:04:33',NULL,1),(44,0,0,1,'Joanna',44,'2023-05-08 16:31:35',NULL,1),(45,0,0,1,'Joanna',45,'2023-05-08 19:21:12',NULL,1),(46,1,0,1,'Joanna',46,'2023-05-11 20:16:11','2023-05-11 20:23:55',0),(47,0,0,1,'Joanna',47,'2023-05-11 21:04:30',NULL,1),(48,0,0,1,'Joanna',48,'2023-05-12 11:46:23',NULL,1),(49,0,0,1,'Joanna',49,'2023-05-12 19:39:01',NULL,1),(50,0,0,1,'Joanna',50,'2023-05-12 19:41:43',NULL,1),(51,0,0,1,'Joanna',51,'2023-05-12 19:50:14',NULL,1),(52,0,0,1,'Joanna',52,'2023-05-13 10:45:18',NULL,1),(53,0,0,1,'Joanna',53,'2023-05-14 11:20:37',NULL,1),(54,0,0,1,'Joanna',54,'2023-05-14 14:45:49',NULL,1),(55,0,0,1,'Joanna',55,'2023-05-14 14:48:21',NULL,1),(56,0,0,1,'Joanna',56,'2023-05-18 11:05:46',NULL,1);
/*!40000 ALTER TABLE `user_setting` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-05-19 16:00:11
