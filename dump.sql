-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: localhost    Database: timbangan
-- ------------------------------------------------------
-- Server version	8.0.45

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
-- Table structure for table `data_timbang`
--

DROP TABLE IF EXISTS `data_timbang`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `data_timbang` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tanggal_upload` datetime DEFAULT CURRENT_TIMESTAMP,
  `No` int DEFAULT NULL,
  `Type` varchar(50) DEFAULT NULL,
  `Status` varchar(50) DEFAULT NULL,
  `Nomor_SPMSPB` int DEFAULT NULL,
  `Nomor_SPPB` int DEFAULT NULL,
  `Nomor_SPT` varchar(50) DEFAULT NULL,
  `Nomor_SPTA` varchar(50) DEFAULT NULL,
  `Nomor_SO` varchar(50) DEFAULT NULL,
  `Nomor_PO` varchar(50) DEFAULT NULL,
  `Nomor_GRPO` varchar(50) DEFAULT NULL,
  `Nomor_Surat_Jalan` varchar(100) DEFAULT NULL,
  `CardName` varchar(255) DEFAULT NULL,
  `ItemCode` varchar(50) DEFAULT NULL,
  `ItemName` varchar(255) DEFAULT NULL,
  `Batch` varchar(50) DEFAULT NULL,
  `Qty_SJ` int DEFAULT NULL,
  `Qty_SPMSPB` int DEFAULT NULL,
  `Remarks` text,
  `Tanggal_Masuk` varchar(50) DEFAULT NULL,
  `Berat_Masuk` int DEFAULT NULL,
  `Jam_Masuk` varchar(50) DEFAULT NULL,
  `Tanggal_Keluar` varchar(50) DEFAULT NULL,
  `Berat_Keluar` int DEFAULT NULL,
  `Jam_Keluar` varchar(50) DEFAULT NULL,
  `Tanggal_Loading_Mulai` varchar(50) DEFAULT NULL,
  `Jam_Loading_Mulai` varchar(50) DEFAULT NULL,
  `Tanggal_Loading_Selesai` varchar(50) DEFAULT NULL,
  `Jam_Loading_Selesai` varchar(50) DEFAULT NULL,
  `Supir` varchar(50) DEFAULT NULL,
  `Transportir` varchar(50) DEFAULT NULL,
  `Kendaraan` varchar(50) DEFAULT NULL,
  `Nopol` varchar(50) DEFAULT NULL,
  `Tipe` int DEFAULT NULL,
  `CardCode` varchar(50) DEFAULT NULL,
  `Shift` int DEFAULT NULL,
  `Qty_sblm_Rafaksi` int DEFAULT NULL,
  `Persentase_Potongan_Rafaksi` int DEFAULT NULL,
  `Qty_Rafaksi` int DEFAULT NULL,
  `Qty_Netto` int DEFAULT NULL,
  `NoSystem` int DEFAULT NULL,
  `Kode_Pos_Insentif_Jarak` int DEFAULT NULL,
  `Nama_Pos_Insentif_Jarak` varchar(50) DEFAULT NULL,
  `Jumlah_Karung` int DEFAULT NULL,
  `Berat_rata2_Karung` varchar(50) DEFAULT NULL,
  `YEARSJ` int DEFAULT NULL,
  `MONTHSJ` int DEFAULT NULL,
  `DATESJ` int DEFAULT NULL,
  `NOHP` varchar(50) DEFAULT NULL,
  `SJENTRY` int DEFAULT NULL,
  `NOFAX` varchar(50) DEFAULT NULL,
  `NoDelivery` int DEFAULT NULL,
  `MbsToWeighbridge(Minute)` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=168007 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'timbangan'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-14 21:45:46
