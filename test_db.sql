BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "intervals" (
	"account_number"	text NOT NULL,
	"start_date"	date NOT NULL,
	"end_date"	 NOT NULL
);
CREATE TABLE IF NOT EXISTS "accounts" (
	"account_number"	text NOT NULL,
	"login_name"	text,
	"backend_config"	TEXT NOT NULL DEFAULT '{}',
	"bank_code"	TEXT NOT NULL,
	"preferred_backend"	TEXT,
	"initial_balance"	INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "transactions" (
	"id"	INTEGER,
	"local_account"	text NOT NULL,
	"remote_account"	text NOT NULL,
	"remote_name"	text NOT NULL,
	"entry_date"	date NOT NULL,
	"valuta_date"	date NOT NULL,
	"value"	integer NOT NULL,
	"currency"	text NOT NULL,
	"purpose"	text NOT NULL,
	"primanota"	text NOT NULL,
	"transaction_key"	text NOT NULL,
	"transaction_code"	text NOT NULL,
	"transaction_text"	text NOT NULL,
	"creditor_scheme_id"	text NOT NULL,
	"mandate_id"	text NOT NULL,
	"end_to_end_ref"	text NOT NULL,
	"total_order"	integer NOT NULL,
	"inserted_at"	datetime NOT NULL,
	"ultimate_debtor"	BLOB NOT NULL,
	"ultimate_creditor"	TEXT NOT NULL,
	"inserted_by"	TEXT NOT NULL,
	"original_value"	INTEGER,
	"original_currency"	TEXT,
	"exchange_rate"	TEXT,
	"cc_entry_ref"	TEXT,
	"cc_billing_ref"	TEXT,
	"matching_txn"	INTEGER,
	FOREIGN KEY("matching_txn") REFERENCES "transactions"("id"),
	UNIQUE("local_account","total_order"),
	FOREIGN KEY("local_account") REFERENCES "accounts"("account_number"),
	PRIMARY KEY("id")
);
INSERT INTO "intervals" VALUES ('iban:DE76500105172922398822','2021-06-01','2021-06-06');
INSERT INTO "intervals" VALUES ('iban:DE76500105172922398822','2021-06-10','2021-06-18');
INSERT INTO "intervals" VALUES ('iban:DE36500105178641165783','2022-06-07','2023-09-28');
INSERT INTO "intervals" VALUES ('cc:4545454258246464','2022-09-26','2023-09-28');

INSERT INTO "accounts" VALUES ('iban:DE76500105172922398822','','','12345678',NULL,78530);
INSERT INTO "accounts" VALUES ('iban:DE36500105178641165783','','','87654321',NULL,3577484);
INSERT INTO "accounts" VALUES ('iban:DE40500105177993743285',NULL,'{}','12312312',NULL,0);
INSERT INTO "accounts" VALUES ('cc:4545454258246464','','','12345678','fints',-10298);

-- DE76500105172922398822
INSERT INTO "transactions" VALUES (1,'iban:DE76500105172922398822','iban:DE66500105174379953982','Max Vermieter','2021-06-01','2021-06-01',-46000,'EUR','Miete','7000','012','117','DAUERAUFTRAG','','','',0,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2,'iban:DE76500105172922398822','iban:DE14500105174395846913','Gemeinnützige Organisation','2021-06-01','2021-06-01',-5000,'EUR','','7000','012','117','DAUERAUFTRAG','','','',1,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (3,'iban:DE76500105172922398822','iban:DE42500105171144643283','Stromanbieter','2021-06-01','2021-06-01',1654,'EUR','Vertragskonto 2002152559 Darmstadt, Am Blauen Stein 11 Rechnung vom 27.05.2021','9249','062','166','GUTSCHR. UEBERWEISUNG','','','2002152559 220015933235',2,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (4,'iban:DE76500105172922398822','iban:DE73500105173129753642','Supermark 1','2021-06-03','2021-06-03',-3141,'EUR','2021-06-02T17.38Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',3,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (5,'iban:DE76500105172922398822','iban:DE73500105173129753642','Supermark 1','2021-06-07','2021-06-07',-4110,'EUR','2021-06-05T17.48Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',4,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (6,'iban:DE76500105172922398822','iban:DE39500105172737595282','Kaufhaus','2021-06-09','2021-06-09',-1309,'EUR','2021-06-08T17.57Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',5,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (7,'iban:DE76500105172922398822','iban:DE76500105172284438261','Meine Bank','2021-06-10','2021-06-10',-15846,'EUR','VISA NR.  454545XXXXXX6464 KREDITKARTEN-ABR. VOM 04.06','7198','010','6','EIGENE KREDITKARTENABRECHN.','','','',6,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (8,'iban:DE76500105172922398822','iban:DE73500105173129753642','Supermark 1','2021-06-03','2021-06-03',-1899,'EUR','2021-06-09T18.03Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',7,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);

INSERT INTO "transactions" VALUES (9,'iban:DE76500105172922398822','iban:DE47500105179422158563','PayPal (Europe) S.a.r.l. et Cie., S.C.A.','2021-06-11','2021-06-11',-4495,'EUR','PP.1937.PP . SDFGHJKJHG, Ihr Einkauf bei SDFGHJKJHG','9248','DDT','105','FOLGELASTSCHRIFT','LU23XXX0000000000000000045','3X22XUXXUI45X','1020334190400 PP.1937.PP PAYPAL',8,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (10,'iban:DE76500105172922398822','iban:DE73500105173129753642','Supermark 1','2021-06-14','2021-06-14',-3683,'EUR','2021-06-11T13.25Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',9,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (11,'iban:DE76500105172922398822','iban:DE02500105178244556675','Krankenkasse','2021-06-15','2021-06-15',-11069,'EUR','BuchNr 18382284857Monat 05/21 T357566355 Beitraege','9248','DDT','105','FOLGELASTSCHRIFT','DE98OT302299999937','XXXXXXXXXXX','29384792',10,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (12,'iban:DE76500105172922398822','iban:DE36500105173825381757','Gemeinnützige Organisation','2021-06-15','2021-06-15',-5000,'EUR','Vielen Dank fur Ihre Spende','9248','DDT','105','FOLGELASTSCHRIFT','DE99PO09809234234','ALKSJD2908374920','2938749283749',11,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (13,'iban:DE76500105172922398822','iban:DE83500105173932364636','Klient','2021-06-15','2021-06-15',50000,'EUR','Rechnung 2021-05-01','9249','062','166','GUTSCHR. UEBERWEISUNG','','','KJH.098.PO.1230948',12,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (14,'iban:DE76500105172922398822','iban:DE02500105175819235411','Handy Deutschland GmbH','2021-06-16','2021-06-16',-3009,'EUR','Kundennummer 239084234/RG 02938423 vom 09.06.21','9248','DDT','105','FOLGELASTSCHRIFT','DE55XXX2039429034','LK023948','2039840923',13,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (15,'iban:DE76500105172922398822','iban:DE73500105173129753642','Supermark 1','2021-06-17','2021-06-17',-3170,'EUR','2021-06-16T21.41Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',14,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (16,'iban:DE76500105172922398822','iban:DE83500105173932364636','Klient','2021-06-18','2021-06-18',280750,'EUR','Rechnung 2021-05-12','9249','062','166','GUTSCHR. UEBERWEISUNG','','','POI.123.PO.230948',15,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);

INSERT INTO "transactions" VALUES (17,'iban:DE76500105172922398822','iban:DE73500105173129753642','Supermark 1','2021-06-21','2021-06-21',-3603,'EUR','2021-06-19T18.51Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',16,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (18,'iban:DE76500105172922398822','iban:DE49500105174485717171','Bank','2021-06-21','2021-06-21',-1500,'EUR','2021-06-19T11.09Debitk.0 2023-12','9208','032','106','BARGELDAUSZAHLUNG','','','',17,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (19,'iban:DE76500105172922398822','iban:DE47500105179422158563','PayPal (Europe) S.a.r.l. et Cie., S.C.A.','2021-06-23','2021-06-23',-10499,'EUR','PP.1239809.PP . QWERTZUI, Ihr Einkauf bei QWERTZUI','9248','DDT','105','FOLGELASTSCHRIFT','LU23XXX0000000000000000045','3X22XUXXUI45X','1772717778787 PP.1937.PP PAYPAL',18,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (20,'iban:DE76500105172922398822','iban:DE61500105172649479989','HEALTH GMBH','2021-06-24','2021-06-24',-42154,'EUR','Nr. 2398473242, Hinz KunzDATUM 24.06.2021, 11.42 UHR','9310','033','177','ONLINE-UEBERWEISUNG','','','',19,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (21,'iban:DE76500105172922398822','iban:DE73500105173129753642','Supermark 1','2021-06-25','2021-06-25',-4650,'EUR','2021-06-24T19.20Debitk.0 2023-12','9248','037','106','KARTENZAHLUNG','','','',20,'2023-07-04 20:16:42.863249','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);


-- DE36500105178641165783
INSERT INTO "transactions" VALUES (2403,'iban:DE36500105178641165783','iban:DE76500105172922398822','Ich (Privat)','2023-09-26','2023-09-26',-300000,'EUR','Privatentnahme','','TRF','116','','','','NOTPROVIDED',42,'2023-09-27 10:45:20.023160','','','aqbanking',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2488,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-06-07','2022-06-07',233047,'EUR','Gehalt 12342342','','','','Auslandsüberweisung','','','',0,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2489,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2022-06-15','2022-06-15',-200000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',1,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2490,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-06-15','2022-06-15',871592,'EUR','Gehalt 982374','','','','Auslandsüberweisung','','','',2,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2491,'iban:DE36500105178641165783','iban:DE76500105172922398822','Ich (privat)','2022-07-04','2022-07-04',-100000,'EUR','S-34534/DE76500105172922398822 Privatentnahme','','','','SEPA Überweisung','','','',3,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2492,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2022-07-15','2022-07-15',-300000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',4,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2493,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-07-15','2022-07-15',908248,'EUR','Gehalt 0123941234','','','','Auslandsüberweisung','','','',5,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2494,'iban:DE36500105178641165783','iban:DE76500105172922398822','Ich (privat)','2022-08-15','2022-08-15',-100000,'EUR','S-67867/DE76500105172922398822 Privatentnahme','','','','SEPA Überweisung','','','',6,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2495,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2022-08-15','2022-08-15',-300000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',7,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2496,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-08-15','2022-08-15',895152,'EUR','Gehalt 230948','','','','Auslandsüberweisung','','','',8,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2497,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-08-31','2022-08-31',99405,'EUR','Gehalt 029348','','','','Auslandsüberweisung','','','',9,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2498,'iban:DE36500105178641165783','?:;','','2022-08-31','2022-08-31',-170,'EUR','','','','','Sonstige','','','',10,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2499,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-09-07','2022-09-06',251275,'EUR','Gehalt 098324','','','','Auslandsüberweisung','','','',11,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2500,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2022-09-15','2022-09-15',-400000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',12,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2501,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-09-15','2022-09-15',915147,'EUR','Gehalt 0239084234','','','','Auslandsüberweisung','','','',13,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2502,'iban:DE36500105178641165783','?:;','','2022-09-30','2022-09-30',-85,'EUR','','','','','Sonstige','','','',14,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2503,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2022-10-14','2022-10-14',-400000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',15,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2504,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-10-17','2022-10-14',936773,'EUR','Gehalt 0293842348','','','','Auslandsüberweisung','','','',16,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2505,'iban:DE36500105178641165783','?:;','','2022-10-31','2022-10-31',-85,'EUR','','','','','Sonstige','','','',17,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2506,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2022-11-15','2022-11-15',-400000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',18,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2507,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-11-15','2022-11-15',877439,'EUR','Gehalt 203458793','','','','Auslandsüberweisung','','','',19,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2508,'iban:DE36500105178641165783','?:;','','2022-11-30','2022-11-30',-85,'EUR','','','','','Sonstige','','','',20,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2509,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-12-14','2022-12-13',93137,'EUR','Gehalt 098098098','','','','Auslandsüberweisung','','','',21,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2510,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2022-12-15','2022-12-15',-400000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',22,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2511,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-12-15','2022-12-15',860292,'EUR','Gehalt 234234234','','','','Auslandsüberweisung','','','',23,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2512,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-12-20','2022-12-20',233747,'EUR','Gehalt 7654909','','','','Auslandsüberweisung','','','',24,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2513,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2022-12-27','2022-12-23',857472,'EUR','Gehalt 988236753458','','','','Auslandsüberweisung','','','',25,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2514,'iban:DE36500105178641165783','?:;','','2022-12-30','2022-12-31',-85,'EUR','','','','','Sonstige','','','',26,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2515,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2023-01-13','2023-01-13',-400000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',27,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2516,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2023-01-13','2023-01-13',845047,'EUR','Gehalt 88989223','','','','Auslandsüberweisung','','','',28,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2517,'iban:DE36500105178641165783','iban:DE76500105172922398822','Ich privat','2023-01-26','2023-01-26',-2000000,'EUR','234JH/DE76500105172922398822','','','','SEPA Überweisung','','','',29,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2518,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2023-02-15','2023-02-15',-400000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',30,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2519,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2023-02-15','2023-02-15',921107,'EUR','Gehalt 9999222','','','','Auslandsüberweisung','','','',31,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2520,'iban:DE36500105178641165783','iban:DE76500105172922398822','ICH (PRIVAT)','2023-03-15','2023-03-15',-400000,'EUR','PRIVATENTNAHME','','','','SEPA Überweisung (Dauerauftrag)','','','',32,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "transactions" VALUES (2521,'iban:DE36500105178641165783','?:;524565855','COMPANY, INC.','2023-03-15','2023-03-15',932308,'EUR','Gehalt 111214428','','','','Auslandsüberweisung','','','',33,'2023-09-28 17:24:54.037049','','','csv',NULL,NULL,NULL,NULL,NULL,NULL);


INSERT INTO "transactions" VALUES (2210,'cc:4545454258246464','','','2022-09-26','2022-09-24',899,'EUR','AMZNPrime DEamzn.de/info LU','','','','','','','',0,'2023-09-25 20:47:40.013580','','','fints',899,'EUR','1','269001301510001','20221004',NULL);
INSERT INTO "transactions" VALUES (2211,'cc:4545454258246464','','','2022-09-26','2022-09-24',399,'EUR','Prime Video234-12345677','','','','','','','',1,'2023-09-25 20:47:40.013580','','','fints',399,'EUR','1','269001302870002','20221004',NULL);
INSERT INTO "transactions" VALUES (2212,'cc:4545454258246464','','','2022-10-04','2022-10-01',-799,'EUR','NETFLIX.COM  DE','','','','','','','',2,'2023-09-25 20:47:40.013580','','','fints',-799,'EUR','1','277002570950001','20221004',NULL);
INSERT INTO "transactions" VALUES (2213,'cc:4545454258246464','','','2022-10-04','2022-10-04',9799,'EUR','Einzug des Rechnungsbetrages','','','','','','','',3,'2023-09-25 20:47:40.013580','','','fints',9799,'EUR','1','277980781120002','20221004',NULL);
INSERT INTO "transactions" VALUES (2214,'cc:4545454258246464','','','2022-10-26','2022-10-23',-1490,'EUR','EPOCH  *mixmatchGmAT           AT','','','','','','','',4,'2023-09-25 20:47:40.013580','','','fints',-1490,'EUR','1','299000550140001','20221104',NULL);
INSERT INTO "transactions" VALUES (2215,'cc:4545454258246464','','','2022-10-31','2022-10-29',-399,'EUR','Prime Video *2319847-2309840239','','','','','','','',5,'2023-09-25 20:47:40.013580','','','fints',-399,'EUR','1','304001441870001','20221104',NULL);
INSERT INTO "transactions" VALUES (2216,'cc:4545454258246464','','','2022-10-31','2022-10-29',-1999,'EUR','STEAMGAMES.COM DE','','','','','','','',6,'2023-09-25 20:47:40.013580','','','fints',-1999,'EUR','1','304001496270002','20221104',NULL);
INSERT INTO "transactions" VALUES (2217,'cc:4545454258246464','','','2022-11-02','2022-11-01',-799,'EUR','NETFLIX.COM  DE','','','','','','','',7,'2023-09-25 20:47:40.013580','','','fints',-799,'EUR','1','306000868930001','20221104',NULL);
INSERT INTO "transactions" VALUES (2218,'cc:4545454258246464','','','2022-11-03','2022-11-02',-499,'EUR','Prime Video *PO230948-213094234','','','','','','','',8,'2023-09-25 20:47:40.013580','','','fints',-499,'EUR','1','307000546160001','20221104',NULL);
INSERT INTO "transactions" VALUES (2219,'cc:4545454258246464','','','2022-11-04','2022-11-04',5186,'EUR','Einzug des Rechnungsbetrages','','','','','','','',9,'2023-09-25 20:47:40.013580','','','fints',5186,'EUR','1','308980625250001','20221104',NULL);
INSERT INTO "transactions" VALUES (2220,'cc:4545454258246464','','','2022-11-07','2022-11-05',-299,'EUR','Prime Video *42342342-090923423','','','','','','','',10,'2023-09-25 20:47:40.013580','','','fints',-299,'EUR','1','311001240060001','20221204',NULL);
INSERT INTO "transactions" VALUES (2221,'cc:4545454258246464','','','2022-11-07','2022-11-05',-299,'EUR','Prime Video *021394234-0912374982345','','','','','','','',11,'2023-09-25 20:47:40.013580','','','fints',-299,'EUR','1','311001240910002','20221204',NULL);
INSERT INTO "transactions" VALUES (2222,'cc:4545454258246464','','','2022-11-07','2022-11-05',299,'EUR','Prime Video OI-23094823','','','','','','','',12,'2023-09-25 20:47:40.013580','','','fints',299,'EUR','1','311001308110003','20221204',NULL);
INSERT INTO "transactions" VALUES (2223,'cc:4545454258246464','','','2022-11-10','2022-11-09',-4954,'EUR','Amazon.deAMAZON.DE    LU','','','','','','','',13,'2023-09-25 20:47:40.013580','','','fints',-4954,'EUR','1','314000281500001','20221204',NULL);
INSERT INTO "transactions" VALUES (2224,'cc:4545454258246464','','','2022-11-21','2022-11-19',-13590,'EUR','AMZ*PROCAVEamazonpaymentLU','','','','','','','',14,'2023-09-25 20:47:40.013580','','','fints',-13590,'EUR','1','325001544490001','20221204',NULL);
INSERT INTO "transactions" VALUES (2225,'cc:4545454258246464','','','2022-12-02','2022-12-01',-799,'EUR','NETFLIX.COM  DE','','','','','','','',15,'2023-09-25 20:47:40.013580','','','fints',-799,'EUR','1','336000347700001','20221204',NULL);
INSERT INTO "transactions" VALUES (2226,'cc:4545454258246464','','','2022-12-02','2022-12-04',19642,'EUR','Einzug des Rechnungsbetrages','','','','','','','',16,'2023-09-25 20:47:40.013580','','','fints',19642,'EUR','1','336980593580002','20221204',NULL);
INSERT INTO "transactions" VALUES (2227,'cc:4545454258246464','','','2022-12-20','2022-12-19',-9695,'EUR','DB Vertrieb GmbHKLJASD       DE','','','','','','','',17,'2023-09-25 20:47:40.013580','','','fints',-9695,'EUR','1','354000457600001','20230104',NULL);
INSERT INTO "transactions" VALUES (2228,'cc:4545454258246464','','','2022-12-29','2022-12-28',-8915,'EUR','DB Vertrieb GmbHLKJGZZ       DE','','','','','','','',18,'2023-09-25 20:47:40.013580','','','fints',-8915,'EUR','1','363000593790001','20230104',NULL);
INSERT INTO "transactions" VALUES (2229,'cc:4545454258246464','','','2022-12-30','2022-12-29',-2899,'EUR','Prime Video *87823823458238-9823447532','','','','','','','',19,'2023-09-25 20:47:40.013580','','','fints',-2899,'EUR','1','364000496550001','20230104',NULL);
INSERT INTO "transactions" VALUES (2230,'cc:4545454258246464','','','2023-01-02','2023-01-01',-799,'EUR','NETFLIX.COM  DE','','','','','','','',20,'2023-09-25 20:47:40.013580','','','fints',-799,'EUR','1','002002706730001','20230104',NULL);
INSERT INTO "transactions" VALUES (2231,'cc:4545454258246464','','','2023-01-04','2023-01-04',22308,'EUR','Einzug des Rechnungsbetrages','','','','','','','',21,'2023-09-25 20:47:40.013580','','','fints',22308,'EUR','1','004980663010001','20230104',NULL);
INSERT INTO "transactions" VALUES (2232,'cc:4545454258246464','','','2023-01-13','2023-01-12',-11497,'EUR','AMZN Mktp DE*2001947856-123-123123 LU','','','','','','','',22,'2023-09-25 20:47:40.013580','','','fints',-11497,'EUR','1','013000323990001','20230204',NULL);
INSERT INTO "transactions" VALUES (2233,'cc:4545454258246464','','','2023-02-01','2023-02-01',-799,'EUR','NETFLIX.COM  DE','','','','','','','',23,'2023-09-25 20:47:40.013580','','','fints',-799,'EUR','1','032000728540001','20230204',NULL);
INSERT INTO "transactions" VALUES (2234,'cc:4545454258246464','','','2023-02-03','2023-02-04',12296,'EUR','Einzug des Rechnungsbetrages','','','','','','','',24,'2023-09-25 20:47:40.013580','','','fints',12296,'EUR','1','034980631960001','20230204',NULL);
INSERT INTO "transactions" VALUES (2235,'cc:4545454258246464','','','2023-02-07','2023-02-06',-2990,'EUR','AMZN Mktp DE*987654-734-123412 LU','','','','','','','',25,'2023-09-25 20:47:40.013580','','','fints',-2990,'EUR','1','038000514500001','20230304',NULL);
INSERT INTO "transactions" VALUES (2236,'cc:4545454258246464','','','2023-02-14','2023-02-13',-6970,'EUR','AMZN Mktp DE*8888234-230948-12341 LU','','','','','','','',26,'2023-09-25 20:47:40.013580','','','fints',-6970,'EUR','1','045000698410001','20230304',NULL);
COMMIT;
