using System;
using Microsoft.EntityFrameworkCore.Migrations;

namespace HRMS.DAL.EFCore.Migrations

   public partial class HRMSDatabase_v1 : Migration
   {
       protected override void Up(MigrationBuilder migrationBuilder)
       {
           migrationBuilder.CreateTable(
               name: "Address",
               columns: table => new
               {
                   EmployeeAddressId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeId = table.Column<int>(nullable: false),
                   PstreeOne = table.Column<string>(maxLength: 50, nullable: false),
                   PstreeTwo = table.Column<string>(maxLength: 50, nullable: false),
                   Pcity = table.Column<string>(maxLength: 25, nullable: false),
                   PState = table.Column<string>(maxLength: 25, nullable: false),
                   PpostalCode = table.Column<string>(maxLength: 6, nullable: false),
                   CstreeOne = table.Column<string>(maxLength: 50, nullable: false),
                   CstreeTwo = table.Column<string>(maxLength: 50, nullable: false),
                   Ccity = table.Column<string>(maxLength: 25, nullable: false),
                   CState = table.Column<string>(maxLength: 20, nullable: false),
                   CpostalCode = table.Column<string>(maxLength: 6, nullable: false),
                   LivingDateFrom = table.Column<DateTime>(nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_Address", x => x.EmployeeAddressId);
               });

           migrationBuilder.CreateTable(
               name: "Country",
               columns: table => new
               {
                   CountryId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   CountryName = table.Column<string>(maxLength: 15, nullable: false),
                   SortCode = table.Column<string>(maxLength: 4, nullable: false),
                   IsActive = table.Column<bool>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_Country", x => x.CountryId);
               });

           migrationBuilder.CreateTable(
               name: "Employee",
               columns: table => new
               {
                   EmployeeId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeCode = table.Column<string>(nullable: false),
                   EmployeeDesignation = table.Column<string>(maxLength: 10, nullable: false),
                   DateOfJoining = table.Column<DateTime>(nullable: false),
                   SkillSet = table.Column<string>(nullable: false),
                   CompanyBranchName = table.Column<string>(maxLength: 50, nullable: false),
                   IsOnboardingProgress = table.Column<bool>(nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   LoginId = table.Column<string>(nullable: false),
                   Password = table.Column<string>(nullable: false),
                   UserName = table.Column<string>(nullable: false),
                   Role = table.Column<string>(maxLength: 15, nullable: false),
                   LastLogin = table.Column<DateTime>(nullable: true),
                   MaxAttempt = table.Column<int>(nullable: false),
                   IsLocked = table.Column<bool>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_Employee", x => x.EmployeeId);
               });

           migrationBuilder.CreateTable(
               name: "EmployeeDependent",
               columns: table => new
               {
                   EmployeeDependentId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeId = table.Column<int>(nullable: false),
                   DependentFullName = table.Column<string>(maxLength: 50, nullable: false),
                   DependentRelationship = table.Column<string>(maxLength: 25, nullable: false),
                   DependentDateOfBirth = table.Column<DateTime>(nullable: false),
                   DependentAge = table.Column<string>(maxLength: 8, nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_EmployeeDependent", x => x.EmployeeDependentId);
               });

           migrationBuilder.CreateTable(
               name: "EmployeeDesignations",
               columns: table => new
               {
                   DesignationId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   DesignationName = table.Column<string>(nullable: false),
                   DesignationSort = table.Column<string>(nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_EmployeeDesignations", x => x.DesignationId);
               });

           migrationBuilder.CreateTable(
               name: "EmployeeEducationDetails",
               columns: table => new
               {
                   EmployeeEducationDetailId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeId = table.Column<int>(nullable: false),
                   SchoolCollegeName = table.Column<string>(maxLength: 50, nullable: false),
                   BoardUniversityName = table.Column<string>(maxLength: 50, nullable: false),
                   CourseName = table.Column<string>(maxLength: 20, nullable: false),
                   CourseDetails = table.Column<string>(maxLength: 100, nullable: false),
                   StartDate = table.Column<DateTime>(nullable: false),
                   EndDate = table.Column<DateTime>(nullable: false),
                   TotalMarks = table.Column<string>(nullable: true),
                   ObtainMarks = table.Column<string>(nullable: true),
                   Percentage = table.Column<string>(maxLength: 6, nullable: false),
                   CGPA = table.Column<string>(maxLength: 6, nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_EmployeeEducationDetails", x => x.EmployeeEducationDetailId);
               });

           migrationBuilder.CreateTable(
               name: "EmployeeEPFO",
               columns: table => new
               {
                   EmployeeEPFOId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeId = table.Column<int>(nullable: false),
                   UniversalAccountNumber = table.Column<string>(maxLength: 50, nullable: false),
                   ProvidentFundAccountNumber = table.Column<string>(maxLength: 50, nullable: false),
                   EmployeePensionSchemeNumber = table.Column<string>(maxLength: 50, nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_EmployeeEPFO", x => x.EmployeeEPFOId);
               });

           migrationBuilder.CreateTable(
               name: "EmployeeNominees",
               columns: table => new
               {
                   EmployeeNomineesId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeId = table.Column<int>(nullable: false),
                   NomineeFullName = table.Column<string>(maxLength: 50, nullable: false),
                   NomineeRelationShip = table.Column<string>(maxLength: 25, nullable: false),
                   NomineeDateOfBirth = table.Column<DateTime>(nullable: false),
                   NomineeAge = table.Column<string>(maxLength: 6, nullable: false),
                   ShareInPercentage = table.Column<string>(maxLength: 6, nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_EmployeeNominees", x => x.EmployeeNomineesId);
               });

           migrationBuilder.CreateTable(
               name: "EmployeePersonalDetails",
               columns: table => new
               {
                   EmployeePersonalDetailsId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeId = table.Column<int>(nullable: false),
                   FirstName = table.Column<string>(maxLength: 15, nullable: false),
                   MiddleName = table.Column<string>(maxLength: 15, nullable: false),
                   LastName = table.Column<string>(maxLength: 15, nullable: false),
                   Initials = table.Column<string>(maxLength: 5, nullable: false),
                   EmployeeFullName = table.Column<string>(maxLength: 50, nullable: false),
                   Gender = table.Column<string>(maxLength: 15, nullable: false),
                   MaritalStatus = table.Column<string>(maxLength: 10, nullable: false),
                   DateOfBirth = table.Column<DateTime>(nullable: false),
                   EmployeeAge = table.Column<string>(maxLength: 6, nullable: false),
                   PersonalEmailId = table.Column<string>(maxLength: 25, nullable: false),
                   PrimaryMobile = table.Column<string>(maxLength: 15, nullable: false),
                   SecondaryMobile = table.Column<string>(maxLength: 15, nullable: false),
                   BankIFSC = table.Column<string>(maxLength: 15, nullable: false),
                   BankAccountNumber = table.Column<string>(maxLength: 15, nullable: false),
                   AadharcardNumber = table.Column<string>(maxLength: 15, nullable: false),
                   PANCardNumber = table.Column<string>(maxLength: 12, nullable: false),
                   DrivingNumber = table.Column<string>(maxLength: 15, nullable: true),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_EmployeePersonalDetails", x => x.EmployeePersonalDetailsId);
               });

           migrationBuilder.CreateTable(
               name: "EmployeePreviousCompany",
               columns: table => new
               {
                   PreviousCompanyDetailsId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   EmployeeId = table.Column<int>(nullable: false),
                   CompanyInSequence = table.Column<int>(nullable: false),
                   EmployeePreviousDesignation = table.Column<string>(maxLength: 15, nullable: false),
                   PreviousCompanyName = table.Column<string>(maxLength: 50, nullable: false),
                   CompanyFullAddress = table.Column<string>(maxLength: 100, nullable: false),
                   ContactNumber = table.Column<string>(maxLength: 15, nullable: false),
                   JoiningDate = table.Column<DateTime>(nullable: false),
                   LastDate = table.Column<DateTime>(nullable: false),
                   LeavingReason = table.Column<string>(maxLength: 25, nullable: false),
                   ReportingPersonName = table.Column<string>(maxLength: 25, nullable: false),
                   ReportingPersonDesignation = table.Column<string>(maxLength: 15, nullable: false),
                   ReportingPersonMobileNumber = table.Column<string>(maxLength: 15, nullable: false),
                   IsActive = table.Column<bool>(nullable: false),
                   InsertedBy = table.Column<string>(nullable: false),
                   UpdatedBy = table.Column<string>(nullable: false),
                   InsertDate = table.Column<DateTime>(nullable: false),
                   UpdatedDate = table.Column<DateTime>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_EmployeePreviousCompany", x => x.PreviousCompanyDetailsId);
               });

           migrationBuilder.CreateTable(
               name: "States",
               columns: table => new
               {
                   StateId = table.Column<int>(nullable: false)
                       .Annotation("SqlServer:Identity", "1, 1"),
                   StateName = table.Column<string>(maxLength: 20, nullable: false),
                   SortCode = table.Column<string>(maxLength: 3, nullable: false),
                   CountryId = table.Column<int>(nullable: false),
                   IsActive = table.Column<bool>(nullable: false)
               },
               constraints: table =>
               {
                   table.PrimaryKey("PK_States", x => x.StateId);
               });
       }

       protected override void Down(MigrationBuilder migrationBuilder)
       {
           migrationBuilder.DropTable(
               name: "Address");

           migrationBuilder.DropTable(
               name: "Country");

           migrationBuilder.DropTable(
               name: "Employee");

           migrationBuilder.DropTable(
               name: "EmployeeDependent");

           migrationBuilder.DropTable(
               name: "EmployeeDesignations");

           migrationBuilder.DropTable(
               name: "EmployeeEducationDetails");

           migrationBuilder.DropTable(
               name: "EmployeeEPFO");

           migrationBuilder.DropTable(
               name: "EmployeeNominees");

           migrationBuilder.DropTable(
               name: "EmployeePersonalDetails");

           migrationBuilder.DropTable(
               name: "EmployeePreviousCompany");

           migrationBuilder.DropTable(
               name: "States");
       }
   }