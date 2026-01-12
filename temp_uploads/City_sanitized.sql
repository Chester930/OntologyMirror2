CREATE TABLE "City" (
    [City Key]                   INT               CONSTRAINT "DF_Dimension_City_City_Key"  NOT NULL,
    [WWI City ID]                INT               NOT NULL,
    "City"                       NVARCHAR (50)     NOT NULL,
    [State Province]             NVARCHAR (50)     NOT NULL,
    "Country"                    NVARCHAR (60)     NOT NULL,
    "Continent"                  NVARCHAR (30)     NOT NULL,
    [Sales Territory]            NVARCHAR (50)     NOT NULL,
    "Region"                     NVARCHAR (30)     NOT NULL,
    "Subregion"                  NVARCHAR (30)     NOT NULL,
    "Location"                   "TEXT" NULL,
    [Latest Recorded Population] BIGINT            NOT NULL,
    [Valid From]                 DATETIME2 (7)     NOT NULL,
    [Valid To]                   DATETIME2 (7)     NOT NULL,
    [Lineage Key]                INT               NOT NULL,
    CONSTRAINT "PK_Dimension_City" PRIMARY KEY  ([City Key] ASC)
);
;
CREATE INDEX IF NOT EXISTS "City_IX_Dimension_City_WWICityID" ON "City" ([WWI City ID] ASC, [Valid From] ASC, [Valid To] ASC);
;