# Requirements Document: VaidyaSaarathi

## Introduction

VaidyaSaarathi is a clinical workflow solution that transforms patient intake and triage processes through automated analysis, multi-language support, and role-based access control. The system enables receptionists to capture patient complaints in native languages, nurses to record clinical vitals, and doctors to review AI-generated SOAP notes with risk stratification for efficient patient prioritization.

## Glossary

- **System**: The VaidyaSaarathi application
- **Receptionist**: Healthcare staff responsible for patient registration and initial intake
- **Nurse**: Clinical staff responsible for recording patient vitals and measurements
- **Doctor**: Medical specialist who reviews triage results and makes clinical decisions
- **Patient**: Individual seeking medical care at the healthcare facility
- **SOAP_Note**: Structured clinical documentation (Subjective, Objective, Assessment, Plan)
- **Risk_Score**: Numerical value (0-100) indicating clinical urgency
- **Hospital_ID**: Unique patient identifier within the healthcare system
- **QR_Code**: Machine-readable code containing patient Hospital_ID
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
4. WHERE a user has Receptionist role, THE System SHALL grant access to patient intake and registration features
5. WHERE a user has Nurse role, THE System SHALL grant access to clinical triage input and vitals entry features
6. WHERE a user has Doctor role, THE System SHALL grant access to specialist review, edit, and approval features
7. WHEN a user attempts to access features outside their role permissions, THE System SHALL deny access and display an appropriate error message

### Requirement 2: Patient Identification and History

**User Story:** As a receptionist, I want to quickly identify patients and view their medical history, so that I can provide context-aware intake services.

#### Acceptance Criteria

1. WHEN a receptionist enters a Hospital_ID manually, THE System SHALL retrieve and display the patient's profile within 1 second
2. WHEN a receptionist scans a QR_Code, THE System SHALL extract the Hospital_ID and retrieve the patient's profile within 1 second
3. WHEN displaying a patient profile, THE System SHALL show the patient's name, demographics, and the last 3 to 5 visits with associated diagnoses
4. IF a Hospital_ID does not exist in the system, THEN THE System SHALL display an error message indicating the patient was not found
5. WHEN multiple identification methods are available, THE System SHALL accept both manual entry and QR code scanning interchangeably

### Requirement 3: Multi-Language Patient Intake

**User Story:** As a receptionist, I want to capture patient complaints in their native language using audio recording, so that language barriers do not impede quality care.

#### Acceptance Criteria

1. WHEN a receptionist initiates patient intake, THE System SHALL display a microphone button for audio recording
2. WHEN the microphone button is activated, THE System SHALL record audio in the patient's selected native language
3. WHERE a patient speaks Tamil, Hindi, or other supported languages, THE System SHALL accept and process the audio recording
4. WHEN audio recording completes, THE System SHALL store the audio file with the patient's intake record
5. WHEN the receptionist submits the intake, THE System SHALL initiate backend triage analysis within 1 second

### Requirement 4: Automated Triage Analysis

**User Story:** As a system administrator, I want the backend to automatically analyze patient audio for clinical insights, so that triage quality and speed improve.

#### Acceptance Criteria

1. WHEN audio intake is submitted, THE System SHALL perform acoustic anomaly detection to identify respiratory distress, cough patterns, or voice strain
2. WHEN audio intake is submitted, THE System SHALL transcribe the audio to text in the original language
3. WHEN transcription completes, THE System SHALL translate the text to English for clinical documentation
4. WHEN translation completes, THE System SHALL generate a SOAP_Note from the translated content
5. WHEN SOAP_Note generation completes, THE System SHALL calculate a Risk_Score based on clinical indicators
6. WHEN triage analysis completes, THE System SHALL complete all processing steps within 5 seconds of submission
7. IF triage analysis fails, THEN THE System SHALL log the error and notify the receptionist with a descriptive error message

### Requirement 5: Localized Patient Communication

**User Story:** As a receptionist, I want to provide patients with instructions in their native language, so that they understand their next steps clearly.

#### Acceptance Criteria

1. WHEN triage analysis completes, THE System SHALL generate zone assignment instructions in the patient's native language
2. WHEN localized instructions are generated, THE System SHALL provide a TTS playback button for audio output
3. WHEN the TTS button is activated, THE System SHALL play the instructions in the patient's native language with clear audio quality
4. WHEN displaying instructions, THE System SHALL show both text and audio options simultaneously

### Requirement 6: Clinical Vitals Entry

**User Story:** As a nurse, I want to enter patient vitals and clinical measurements, so that doctors have complete objective data for decision-making.

#### Acceptance Criteria

1. WHEN a nurse accesses a patient record, THE System SHALL display input fields for vital signs including temperature, blood pressure, heart rate, respiratory rate, and oxygen saturation
2. WHEN a nurse enters vital values, THE System SHALL validate that values are within physiologically plausible ranges
3. IF a vital value is outside normal ranges, THEN THE System SHALL display a warning indicator without blocking submission
4. WHEN a nurse submits vitals, THE System SHALL associate the measurements with the patient's current triage record and timestamp the entry
5. WHEN vitals are submitted, THE System SHALL update the Risk_Score if clinical thresholds are exceeded

### Requirement 7: Specialist Dashboard and Queue Management

**User Story:** As a doctor, I want to view a prioritized queue of patients filtered by my specialty, so that I can efficiently manage my workload and address critical cases first.

#### Acceptance Criteria

1. WHEN a doctor accesses their dashboard, THE System SHALL display specialty filter options including Cardiac, Neurology, General Medicine, and Respiratory
2. WHEN a specialty filter is selected, THE System SHALL display only patients assigned to that specialty in the Triage_Queue
3. WHEN displaying the Triage_Queue, THE System SHALL sort patients by Risk_Score in descending order
4. WHEN displaying patient cards in the queue, THE System SHALL color-code cards as Red for Critical (Risk_Score >= 70), Yellow for Urgent (Risk_Score 40-69), and Green for Routine (Risk_Score < 40)
5. WHEN displaying patient cards, THE System SHALL show patient name, chief complaint summary, Risk_Score, and time in queue
6. WHEN the Triage_Queue updates, THE System SHALL refresh the display within 3 seconds to reflect new patients or status changes

### Requirement 8: SOAP Note Review and Editing

**User Story:** As a doctor, I want to review and edit AI-generated SOAP notes, so that I can ensure clinical accuracy before finalizing documentation.

#### Acceptance Criteria

1. WHEN a doctor selects a patient from the Triage_Queue, THE System SHALL display the complete SOAP_Note with Subjective, Objective, Assessment, and Plan sections
2. WHEN viewing a SOAP_Note, THE System SHALL provide inline editing capabilities for all sections
3. WHEN a doctor edits a SOAP_Note, THE System SHALL save changes automatically within 2 seconds of the last keystroke
4. WHEN viewing a SOAP_Note, THE System SHALL display the patient's last visit date and any longitudinal trend alerts
5. WHEN a doctor approves a SOAP_Note, THE System SHALL mark the note as finalized and prevent further edits without explicit unlock action

### Requirement 9: EHR Integration and Export

**User Story:** As a doctor, I want to export finalized SOAP notes to the EHR system, so that patient records remain synchronized across systems.

#### Acceptance Criteria

1. WHEN a doctor finalizes a SOAP_Note, THE System SHALL enable a "Move to EHR" button
2. WHEN the "Move to EHR" button is activated, THE System SHALL generate a FHIR_JSON document containing the patient demographics, SOAP_Note content, vitals, and Risk_Score
3. WHEN FHIR_JSON generation completes, THE System SHALL validate the document against FHIR R4 schema
4. IF FHIR_JSON validation fails, THEN THE System SHALL display validation errors and prevent export
5. WHEN FHIR_JSON validation succeeds, THE System SHALL transmit the document to the configured EHR endpoint
6. WHEN EHR export completes successfully, THE System SHALL mark the patient record as exported and remove it from the active Triage_Queue

### Requirement 10: Analytics and Insights

**User Story:** As a healthcare administrator, I want to view daily statistics and trend analysis, so that I can identify patterns and optimize resource allocation.

#### Acceptance Criteria

1. WHEN an administrator accesses the analytics dashboard, THE System SHALL display daily statistics including total patients triaged, average Risk_Score, and distribution by specialty
2. WHEN displaying daily statistics, THE System SHALL categorize patients by risk level (Critical, Urgent, Routine) with counts and percentages
3. WHEN an administrator selects a trend analysis view, THE System SHALL display time-series graphs showing patient volume and chief complaint frequencies over the selected time period
4. WHEN displaying trend graphs, THE System SHALL allow time period selection of 7 days, 30 days, or 90 days
5. WHEN trend data is requested, THE System SHALL generate visualizations within 3 seconds

### Requirement 11: Data Privacy and Security

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

### Requirement 12: System Performance

**User Story:** As a system user, I want the system to respond quickly to my actions, so that clinical workflows are not delayed.

#### Acceptance Criteria

1. WHEN a user performs any action, THE System SHALL provide visual feedback within 200 milliseconds
2. WHEN triage analysis is initiated, THE System SHALL complete all processing steps within 5 seconds
3. WHEN a user navigates between dashboards, THE System SHALL load the new view within 2 seconds
4. WHEN the Triage_Queue contains up to 100 patients, THE System SHALL render the queue within 1 second
5. WHEN concurrent users reach 50, THE System SHALL maintain response times within the specified thresholds for all operations
