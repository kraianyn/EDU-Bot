CREATE TABLE "EDUs" (
	"id" INTEGER NOT NULL UNIQUE,
	"name" TEXT NOT NULL UNIQUE,
	"city" TEXT NOT NULL,
	"departments" TEXT NOT NULL,
	PRIMARY KEY("id")
);

CREATE TABLE "groups" (
	"id" INTEGER NOT NULL UNIQUE,
	"name" TEXT NOT NULL,
	"graduation" INTEGER,
	"info" TEXT,
	"events" TEXT,
	PRIMARY KEY("id")
);

CREATE TABLE "chats" (
	"id" INTEGER NOT NULL UNIQUE,
	"type" INTEGER NOT NULL,
	"username" TEXT NOT NULL,
	"language" INTEGER NOT NULL,
	"group_id" INTEGER NOT NULL,
	"role" INTEGER,
	"familiarity" TEXT,
	"feedback" TEXT,
	"registered" TEXT NOT NULL,
	PRIMARY KEY("id")
);

CREATE TABLE "ecampus" (
	"id" INTEGER NOT NULL UNIQUE,
	"login" TEXT NOT NULL UNIQUE,
	"password" TEXT NOT NULL,
	"points" TEXT,
	PRIMARY KEY("id", "login")
);