# Requirements Document: VaidyaSaarathi

## Introduction

VaidyaSaarathi is a clinical workflow solution that transforms patient intake and triage processes through automated analysis, multi-language support, and role-based access control. The system enables nurses to capture patient complaints in native languages along with clinical vitals, and doctors to review AI-generated SOAP notes with risk stratification for efficient patient prioritization.

## Glossary

- **System**: The VaidyaSaarathi application
- **Nurse**: Healthcare staff responsible for patient registration, initial intake, recording vitals, and capturing patient complaints
- **Doctor**: Medical specialist who reviews triage results and makes clinical decisions
- **Patient**: Individual seeking medical care at the healthcare facility
- **SOAP_Note**: Structured clinical documentation (Subjective, Objective, Assessment, Plan)
- **Risk_Score**: Numerical value (0-100) indicating clinical urgency
- **Patient_ID**: Unique patient identifier within the healthcare system
- **Triage_Queue**: Ordered list of patients awaiting specialist review
- **FHIR_JSON**: Fast Healthcare Interoperability Resources JSON format
- **EHR**: Electronic Health Record system
- **SSO**: Single Sign-On authentication mechanism
- **TTS**: Text-to-Speech audio synthesis
- **PII**: Personally Identifiable Information
- **HIPAA**: Health Insurance Portability and Accountability Act

## Requirements

### Requirement 1: Authentication and Authorization

**User Story:** As a healthcare worker, I want to log in with my hospital credentials and access only the features relevant to my role, so that I can perform my duties efficiently and securely.

#### Acceptance Criteria

1. WHEN a user accesses the system, THE System SHALL display a mock SSO login screen requesting Hospital ID credentials
2. WHEN a user submits valid credentials, THE System SHALL authenticate the user and determine their assigned role
3. WHEN authentication succeeds, THE System SHALL redirect the user to their role-specific dashboard within 2 seconds
4. WHERE a user has Nurse role, THE System SHALL grant access to patient intake, vitals entry, and audio recording features
5. WHERE a user has Doctor role, THE System SHALL grant access to specialist review, edit, and approval features
6. WHEN a user attempts to access features outside their role permissions, THE System SHALL deny access and display an appropriate error message

### Requirement 2: Patient Identification and Complete Intake

**User Story:** As a Nurse, I want to quickly enter a patient ID, capture their vitals, and record their complaint audio in one workflow, and receive immediate first aid guidance if vitals show abnormalities, so that I can provide appropriate immediate care while the case is queued for doctor review.

#### Acceptance Criteria

1. WHEN a nurse enters a Patient_ID, THE System SHALL display an intake form with vitals fields (BP, HR, SpO2, Temp, RR) AND a microphone button for complaint recording
2. THE System SHALL allow recording complaints in Tamil, Hindi, English, or other supported languages
3. WHEN vitals are entered, THE System SHALL validate physiological plausibility and display warnings for out-of-range values without blocking submission
4. WHEN the nurse clicks the microphone button, THE System SHALL start audio recording with a visual timer
5. WHEN the nurse stops recording, THE System SHALL display the recorded audio duration
6. WHEN the intake is submitted (Vitals + Audio), THE System SHALL execute the AI analysis pipeline
7. WHEN AI analysis completes, THE System SHALL display to the nurse:
   - Basic vital check results (normal/abnormal indicators)
   - AI-generated first aid precautions if any vitals show abnormalities
   - Confirmation that the case has been queued for doctor review
8. THE System SHALL NOT display triage zone predictions or complete SOAP notes to nurses (reserved for doctor review)
9. WHEN a triage is successfully submitted, THE System SHALL auto-reset the form for the next patient after 3 seconds

### Requirement 3: AI-Generated First Aid Precautions for Nurses

**User Story:** As a nurse, I want to receive immediate first aid guidance when patient vitals show abnormalities, so that I can provide appropriate immediate care while waiting for doctor review.

#### Acceptance Criteria

1. WHEN vitals analysis detects abnormalities (e.g., high BP, low SpO2, high temperature), THE System SHALL generate context-specific first aid precautions using MedGemma
2. WHEN first aid precautions are generated, THE System SHALL display them in clear, actionable language on the nurse dashboard
3. WHEN vitals are within normal ranges, THE System SHALL display a "No immediate precautions needed" message
4. THE System SHALL include precautions such as:
   - Positioning recommendations (e.g., "Elevate patient's head for breathing difficulty")
   - Monitoring instructions (e.g., "Monitor SpO2 every 5 minutes")
   - When to escalate (e.g., "Call doctor immediately if SpO2 drops below 90%")
5. THE System SHALL NOT include diagnostic conclusions or treatment plans in nurse-facing precautions (reserved for doctor SOAP notes)

### Requirement 4: Automated Triage Analysis for Doctor Review

**User Story:** As a system administrator, I want the backend to automatically analyze patient audio and vitals for comprehensive clinical insights, so that doctors receive complete SOAP notes with triage recommendations.

#### Acceptance Criteria

1. WHEN audio intake is submitted, THE System SHALL perform acoustic anomaly detection to identify respiratory distress, cough patterns, or voice strain
2. WHEN audio intake is submitted, THE System SHALL transcribe the audio to text in the original language
3. WHEN transcription completes, THE System SHALL translate the text to English for clinical documentation
4. WHEN translation completes, THE System SHALL generate a complete SOAP_Note (Subjective, Objective, Assessment, Plan) from the translated content and vitals
5. WHEN SOAP_Note generation completes, THE System SHALL calculate a Risk_Score based on clinical indicators
6. WHEN SOAP_Note generation completes, THE System SHALL assign a Triage_Tier (EMERGENCY, URGENT, SEMI_URGENT, ROUTINE)
7. WHEN triage analysis completes, THE System SHALL complete all processing steps within 25 seconds of submission
8. THE System SHALL make complete SOAP notes and triage tiers available ONLY to doctors (not displayed to nurses)
9. IF triage analysis fails, THEN THE System SHALL log the error and notify the nurse with a descriptive error message

### Requirement 5: Specialist Dashboard and Queue Management

**User Story:** As a doctor, I want to view a prioritized queue of patients filtered by my specialty with complete SOAP notes and triage zones, so that I can efficiently manage my workload and address critical cases first.

#### Acceptance Criteria

1. WHEN a doctor accesses their dashboard, THE System SHALL display specialty filter options including Cardiac, Neurology, General Medicine, and Respiratory
2. WHEN a specialty filter is selected, THE System SHALL display only patients assigned to that specialty in the Triage_Queue
3. WHEN displaying the Triage_Queue, THE System SHALL sort patients by Triage_Tier and Risk_Score (EMERGENCY first, then URGENT, then SEMI_URGENT, then ROUTINE)
4. WHEN displaying patient cards in the queue, THE System SHALL color-code cards as Red for EMERGENCY, Yellow for URGENT, Orange for SEMI_URGENT, and Green for ROUTINE
5. WHEN displaying patient cards, THE System SHALL show patient ID, chief complaint summary, Risk_Score, Triage_Tier, and time in queue
6. WHEN the Triage_Queue updates, THE System SHALL refresh the display within 3 seconds to reflect new patients or status changes
7. WHEN a doctor selects a patient card, THE System SHALL display the complete SOAP note with all four sections and acoustic deviation scores

### Requirement 6: SOAP Note Review and Editing

**User Story:** As a doctor, I want to review and edit AI-generated SOAP notes, so that I can ensure clinical accuracy before finalizing documentation.

#### Acceptance Criteria

1. WHEN a doctor selects a patient from the Triage_Queue, THE System SHALL display the complete SOAP_Note with Subjective, Objective, Assessment, and Plan sections
2. WHEN viewing a SOAP_Note, THE System SHALL provide inline editing capabilities for all sections
3. WHEN a doctor edits a SOAP_Note, THE System SHALL save changes automatically within 2 seconds of the last keystroke
4. WHEN viewing a SOAP_Note, THE System SHALL display the patient's last visit date and any longitudinal trend alerts
5. WHEN a doctor approves a SOAP_Note, THE System SHALL mark the note as finalized and prevent further edits without explicit unlock action

### Requirement 7: EHR Integration and Export

**User Story:** As a doctor, I want to export finalized SOAP notes to the EHR system, so that patient records remain synchronized across systems.

#### Acceptance Criteria

1. WHEN a doctor finalizes a SOAP_Note, THE System SHALL enable a "Move to EHR" button
2. WHEN the "Move to EHR" button is activated, THE System SHALL generate a FHIR_JSON document containing the patient demographics, SOAP_Note content, vitals, and Risk_Score
3. WHEN FHIR_JSON generation completes, THE System SHALL validate the document against FHIR R4 schema
4. IF FHIR_JSON validation fails, THEN THE System SHALL display validation errors and prevent export
5. WHEN FHIR_JSON validation succeeds, THE System SHALL transmit the document to the configured EHR endpoint
6. WHEN EHR export completes successfully, THE System SHALL mark the patient record as exported and remove it from the active Triage_Queue

### Requirement 8: Analytics and Insights

**User Story:** As a healthcare administrator, I want to view daily statistics and trend analysis, so that I can identify patterns and optimize resource allocation.

#### Acceptance Criteria

1. WHEN an administrator accesses the analytics dashboard, THE System SHALL display daily statistics including total patients triaged, average Risk_Score, and distribution by specialty
2. WHEN displaying daily statistics, THE System SHALL categorize patients by risk level (Critical, Urgent, Routine) with counts and percentages
3. WHEN an administrator selects a trend analysis view, THE System SHALL display time-series graphs showing patient volume and chief complaint frequencies over the selected time period
4. WHEN displaying trend graphs, THE System SHALL allow time period selection of 7 days, 30 days, or 90 days
5. WHEN trend data is requested, THE System SHALL generate visualizations within 3 seconds

### Requirement 9: Data Privacy and Security

**User Story:** As a compliance officer, I want patient data to be encrypted and anonymized appropriately, and I want all AI processing to happen locally within the hospital premises, so that the system meets HIPAA requirements and ensures complete data sovereignty.

#### Acceptance Criteria

1. WHEN patient data is stored, THE System SHALL encrypt all PII using AES-256 encryption at rest
2. WHEN patient data is transmitted, THE System SHALL use TLS 1.2 or higher for all network communications
3. WHEN displaying patient data in analytics dashboards, THE System SHALL mask or anonymize PII to prevent identification
4. WHEN a user accesses patient records, THE System SHALL log the access event with user ID, timestamp, and patient ID for audit purposes
5. WHEN audio recordings are stored, THE System SHALL encrypt the files using AES-256 and restrict access to authorized roles only
6. WHEN a patient record is exported, THE System SHALL include only the minimum necessary data for the intended purpose
7. WHEN processing audio or text data, THE System SHALL use ONLY local AI models running on hospital-owned GPU servers, with NO external API calls for PHI processing
8. WHEN the system is deployed, THE System SHALL support offline operation for core triage workflows (audio intake, transcription, SOAP generation) without requiring internet connectivity
9. WHEN audio files are stored locally, THE System SHALL set file permissions to 0600 (owner read/write only) and directory permissions to 0700 (owner access only)
10. WHEN the system is deployed, THE System SHALL provide an air-gapped deployment option for maximum security in isolated hospital networks

### Requirement 10: System Performance

**User Story:** As a system user, I want the system to respond quickly to my actions, so that clinical workflows are not delayed.

#### Acceptance Criteria

1. WHEN a user performs any action, THE System SHALL provide visual feedback within 200 milliseconds
2. WHEN triage analysis is initiated, THE System SHALL complete all processing steps within 5 seconds
3. WHEN a user navigates between dashboards, THE System SHALL load the new view within 2 seconds
4. WHEN the Triage_Queue contains up to 100 patients, THE System SHALL render the queue within 1 second
5. WHEN concurrent users reach 50, THE System SHALL maintain response times within the specified thresholds for all operations
