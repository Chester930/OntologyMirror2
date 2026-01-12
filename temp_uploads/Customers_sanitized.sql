CREATE TABLE "Customers" (
    "CustomerID"                 INT                                         CONSTRAINT "DF_Sales_Customers_CustomerID"  NOT NULL,
    "CustomerName"               NVARCHAR (100)                              NOT NULL,
    "BillToCustomerID"           INT                                         NOT NULL,
    "CustomerCategoryID"         INT                                         NOT NULL,
    "BuyingGroupID"              INT                                         NULL,
    "PrimaryContactPersonID"     INT                                         NOT NULL,
    "AlternateContactPersonID"   INT                                         NULL,
    "DeliveryMethodID"           INT                                         NOT NULL,
    "DeliveryCityID"             INT                                         NOT NULL,
    "PostalCityID"               INT                                         NOT NULL,
    "CreditLimit"                DECIMAL (18, 2)                             NULL,
    "AccountOpenedDate"          DATE                                        NOT NULL,
    "StandardDiscountPercentage" DECIMAL (18, 3)                             NOT NULL,
    "IsStatementSent"            BIT                                         NOT NULL,
    "IsOnCreditHold"             BIT                                         NOT NULL,
    "PaymentDays"                INT                                         NOT NULL,
    "PhoneNumber"                NVARCHAR (20)                               NOT NULL,
    "FaxNumber"                  NVARCHAR (20)                               NOT NULL,
    "DeliveryRun"                NVARCHAR (5)                                NULL,
    "RunPosition"                NVARCHAR (5)                                NULL,
    "WebsiteURL"                 NVARCHAR (256)                              NOT NULL,
    "DeliveryAddressLine1"       NVARCHAR (60)                               NOT NULL,
    "DeliveryAddressLine2"       NVARCHAR (60)                               NULL,
    "DeliveryPostalCode"         NVARCHAR (10)                               NOT NULL,
    "DeliveryLocation"           "TEXT"                           NULL,
    "PostalAddressLine1"         NVARCHAR (60)                               NOT NULL,
    "PostalAddressLine2"         NVARCHAR (60)                               NULL,
    "PostalPostalCode"           NVARCHAR (10)                               NOT NULL,
    "LastEditedBy"               INT                                         NOT NULL,
    "ValidFrom"                  DATETIME2 (7)  NOT NULL,
    "ValidTo"                    DATETIME2 (7)    NOT NULL,
    CONSTRAINT "PK_Sales_Customers" PRIMARY KEY  ("CustomerID" ASC),
    CONSTRAINT "FK_Sales_Customers_AlternateContactPersonID_Application_People" FOREIGN KEY ("AlternateContactPersonID") REFERENCES "People" ("PersonID"),
    CONSTRAINT "FK_Sales_Customers_Application_People" FOREIGN KEY ("LastEditedBy") REFERENCES "People" ("PersonID"),
    CONSTRAINT "FK_Sales_Customers_BillToCustomerID_Sales_Customers" FOREIGN KEY ("BillToCustomerID") REFERENCES "Customers" ("CustomerID"),
    CONSTRAINT "FK_Sales_Customers_BuyingGroupID_Sales_BuyingGroups" FOREIGN KEY ("BuyingGroupID") REFERENCES "BuyingGroups" ("BuyingGroupID"),
    CONSTRAINT "FK_Sales_Customers_CustomerCategoryID_Sales_CustomerCategories" FOREIGN KEY ("CustomerCategoryID") REFERENCES "CustomerCategories" ("CustomerCategoryID"),
    CONSTRAINT "FK_Sales_Customers_DeliveryCityID_Application_Cities" FOREIGN KEY ("DeliveryCityID") REFERENCES "Cities" ("CityID"),
    CONSTRAINT "FK_Sales_Customers_DeliveryMethodID_Application_DeliveryMethods" FOREIGN KEY ("DeliveryMethodID") REFERENCES "DeliveryMethods" ("DeliveryMethodID"),
    CONSTRAINT "FK_Sales_Customers_PostalCityID_Application_Cities" FOREIGN KEY ("PostalCityID") REFERENCES "Cities" ("CityID"),
    CONSTRAINT "FK_Sales_Customers_PrimaryContactPersonID_Application_People" FOREIGN KEY ("PrimaryContactPersonID") REFERENCES "People" ("PersonID")
)
;
;
CREATE INDEX IF NOT EXISTS "Customers_FK_Sales_Customers_CustomerCategoryID" ON "Customers" ("CustomerCategoryID" ASC);
;
CREATE INDEX IF NOT EXISTS "Customers_FK_Sales_Customers_BuyingGroupID" ON "Customers" ("BuyingGroupID" ASC);
;
CREATE INDEX IF NOT EXISTS "Customers_FK_Sales_Customers_PrimaryContactPersonID" ON "Customers" ("PrimaryContactPersonID" ASC);
;
CREATE INDEX IF NOT EXISTS "Customers_FK_Sales_Customers_AlternateContactPersonID" ON "Customers" ("AlternateContactPersonID" ASC);
;
CREATE INDEX IF NOT EXISTS "Customers_FK_Sales_Customers_DeliveryMethodID" ON "Customers" ("DeliveryMethodID" ASC);
;
CREATE INDEX IF NOT EXISTS "Customers_FK_Sales_Customers_DeliveryCityID" ON "Customers" ("DeliveryCityID" ASC);
;
CREATE INDEX IF NOT EXISTS "Customers_FK_Sales_Customers_PostalCityID" ON "Customers" ("PostalCityID" ASC);
;
CREATE INDEX IF NOT EXISTS "Customers_IX_Sales_Customers_Perf_20160301_06" ON "Customers" ("IsOnCreditHold" ASC, "CustomerID" ASC, "BillToCustomerID" ASC)
    ;
;