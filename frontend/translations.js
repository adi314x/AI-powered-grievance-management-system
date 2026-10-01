// Translation System for Smart Grievance System
// Supports 12 Indian Languages

const translations = {
    en: {
        // Common
        'app_name': 'Smart Grievance System',
        'welcome': 'Welcome',
        'logout': 'Logout',
        'submit': 'Submit',
        'cancel': 'Cancel',
        'save': 'Save',
        'edit': 'Edit',
        'delete': 'Delete',
        'view': 'View',
        'update': 'Update',
        'back': 'Back',
        'next': 'Next',
        'previous': 'Previous',
        'loading': 'Loading...',
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'profile_btn': '👤 Profile',
        'back_to_dashboard': 'Back to Dashboard',
        'back_to_login': 'Back to Login',
        
        // Auth
        'login': 'Login',
        'register': 'Register',
        'email': 'Email',
        'password': 'Password',
        'name': 'Name',
        'phone': 'Phone Number',
        'login_title': 'Login to Your Account',
        'register_title': 'Create New Account',
        'forgot_password': 'Forgot Password?',
        'dont_have_account': "Don't have an account?",
        'already_have_account': 'Already have an account?',
        'verify_email_heading': 'Verify Your Email',
        'enter_verification_code': 'Enter 6-Digit Verification Code',
        'resend_code': 'Resend Code',
        'reset_password': 'Reset Password',
        'new_password': 'New Password',
        'confirm_password': 'Confirm New Password',
        'create_account': 'Create Account',
        'complete_profile': 'Complete Your Profile',
        'complete_profile_desc': 'Please add your missing information to complete your profile. This is required for submitting grievances.',
        'update_now': 'Update Now',
        
        // Dashboard
        'dashboard': 'Dashboard',
        'my_grievances': 'My Grievances',
        'submit_grievance': 'Submit Grievance',
        'track_grievance': 'Track Grievance',
        'profile': 'Profile',
        'total_complaints': 'Total Complaints',
        'resolved': 'Resolved',
        'pending': 'Pending',
        'resolution_rate': 'Resolution Rate',
        'public_dashboard_title': 'Smart Grievance System - Public Dashboard',
        'transparent_stats': 'Transparent Grievance Statistics',
        'realtime_data_desc': 'Real-time aggregated data. No login required.',
        'by_department': 'By Department',
        'dept_breakdown': 'Department-wise Breakdown',
        'hero_title': 'Empowering Citizens, Ensuring Accountability',
        'hero_subtitle': 'Fast, transparent, and ML-assisted grievance redressal for a better tomorrow.',
        'file_complaint': 'File a Complaint',
        'track_status': 'Track Status',
        'resolved_cases': 'Resolved Cases',
        'public_stats': 'View Statistics',
        
        // Grievance
        'complaint_text': 'Describe your complaint',
        'location': 'Location',
        'department': 'Department',
        'status': 'Status',
        'submitted': 'Submitted',
        'submitted_on': 'Submitted On',
        'grievance_id': 'Grievance ID',
        'complaint_details': 'Complaint Details',
        'no_grievances': 'No grievances submitted yet.',
        'no_resolved_cases': 'No resolved cases available yet.',
        'load_error': 'Unable to load data right now.',
        'no_updates': 'No updates yet.',
        'no_comments': 'No comments yet.',
        'original_message': 'Original Message',
        'original_text': 'Original Text',
        'updated_by_label': 'Updated by',
        'auto_translate_hint': '⚠️ Automatic translation for your convenience. Original text available above.',
        'translate_comment': '🌐 Translate this comment...',
        
        // Status keys
        'status_received': 'Received',
        'status_assigned': 'Assigned to Department',
        'status_manual_review': 'Manual Review Required',
        'status_under_progress': 'Under Progress',
        'status_investigation': 'Investigation',
        'status_reviewed': 'Reviewed',
        'status_resolved': 'Resolved',
        'status_closed': 'Closed',
        
        // Roles
        'role_citizen': 'Citizen',
        'role_officer': 'Officer',
        'role_admin': 'Admin',
        'officer_role': '🏛️ OFFICER',
        'admin_role': '⚡ ADMIN',
        'citizen_role': '👤 CITIZEN',
        
        // Form specific
        'mandatory': 'MANDATORY',
        'optional': 'OPTIONAL',
        'mandatory_image_hint': 'At least 1 image is mandatory for this complaint type.',
        'optional_image_hint': 'Images are optional, but helpful for faster verification.',
        'listening_msg': 'Listening... Speak your complaint.',
        'use_gps': '📍 Use GPS',
        'getting_location': 'Getting location...',
        
        // Officer/Admin Specific
        'officer_dashboard': 'Officer Dashboard',
        'admin_dashboard': 'Admin Dashboard',
        'dept_grievances': 'Department Grievances',
        'update_grievance': 'Update Grievance',
        'select_status': 'Select Status',
        'under_progress': 'Under Progress',
        'investigation': 'Investigation',
        'reviewed': 'Reviewed',
        'update_message': 'Update Message',
        'update_details_placeholder': 'Provide details about this update',
        'submit_update': 'Submit Update',
        'comments_and_feedback': 'Comments & Feedback',
        'add_comment': 'Add Comment',
        'post_comment': 'Post Comment',
        'type_comment_placeholder': 'Type your response or feedback...',
        'system_analytics': 'System Analytics',
        'export_excel': '📊 Export to Excel',
        'audit_log': '🔍 Audit Log',
        'create_new_officer': '👤 Create New Officer',
        'all_users_citizens': 'All Users/Citizens',
        'all_officers': 'All Officers',
        'apply_filters': 'Apply Filters',
        'dept_info': '🏛️ Department Information',
        'designation': 'Designation',
        'office_building': 'Office Building',
        'responsibilities': 'Responsibilities',
        'officer_responsibilities_desc': 'Handle & resolve department complaints',
        'office_contact_info': '📞 Office Contact Information',
        'office_phone': 'Office Phone',
        'office_email': 'Office Email',
        'office_location': 'Office Location',
        'personal_information': '📋 Personal Information',
        'full_name': 'Full Name',
        'residential_address_heading': '🏠 Residential Address',
        'address_line': 'Address Line',
        'city': 'City',
        'state': 'State',
        'pincode': 'Pincode',
        'account_details': '🛡️ Account Details',
        'member_since': 'Member Since',
        'account_type': 'Account Type',
        'email_status': 'Email Status',
        'phone_status': 'Phone Status',
        'verified': 'Verified',
        'unverified': 'Unverified',
        'update_btn': 'Update Profile',
        'save_changes': 'Save Changes',
        
        // Departments (Five authorised departments only)
        'roads_public_works': 'Roads and Public Works',
        'water_supply': 'Water Supply',
        'electricity': 'Electricity',
        'sanitation_waste': 'Sanitation and Waste Management',
        'education': 'Education',
        
        // Auth Extended
        'secure_login_portal': 'Secure Login Portal',
        'email_address': 'Email Address',
        'enter_email': 'Enter your email',
        'enter_password': 'Enter your password',
        'register_here': 'Register here',
        'view_public_statistics': '📊 View Public Statistics',
        'join_system': 'Join Smart Grievance System',
        'first_name': 'First Name',
        'enter_first_name': 'First name',
        'last_name': 'Last Name',
        'enter_last_name': 'Last name',
        'phone_number': 'Phone Number',
        'enter_phone': '10-digit mobile number',
        'verified_via_otp': 'Will be verified via OTP',
        'date_of_birth': 'Date of Birth',
        'must_be_18': 'You must be 18 or above to register',
        'gender': 'Gender',
        'select_gender': '-- Select Gender --',
        'male': 'Male / पुरुष',
        'female': 'Female / महिला',
        'other_gender': 'Other / अन्य',
        'prefer_not_to_say': 'Prefer not to say / नहीं बताना चाहते',
        'accepted_gender_values': 'Accepted values: Male, Female, Other, Prefer not to say',
        'create_password': 'Create a strong password',
        'password_requirements': 'Minimum 8 chars with uppercase, lowercase, and number',
        'reenter_password': 'Re-enter password',
        'aadhaar_optional': 'Aadhaar Last 4 Digits (Optional)',
        'last_4_digits': 'Last 4 digits',
        'data_consent': 'I consent to the processing of my data',
        'login_here': 'Login here',
        'view_public_stats': 'View Statistics',
        
        // Dashboards Extended
        'welcome_hero': 'Empowering Citizens, Ensuring Accountability',
        'hero_description': 'Fast, transparent, and ML-assisted grievance redressal for a better tomorrow.',
        'total_grievances': 'Total Complaints',
        'in_progress': 'Under Progress',
        'avg_resolution': 'Avg. Resolution Time',
        'recently_resolved_cases': 'Recently Resolved Cases',
        'resolved_cases_desc': 'Transparency in action: Latest resolved grievances.',
        'submit_new_grievance': 'Submit New Grievance',
        'view_all': 'View All',
        'department_metrics': 'Department Metrics',
        'fraud_alert_system': 'Fraud Alert System',
        'all_statuses': 'All Statuses',
        'all_departments': 'All Departments',
        'search': 'Search',
        'download_report': 'Download Report',
        'select_department': 'Select Department',
        'password_hint': '8+ characters, with uppercase, lowercase, and numbers',
        'address_required': 'Complete Address',
        'address_required_desc': 'Provide full address for site verification',
        'anti_fraud_measures': 'Anti-Fraud Protection',
        'anti_fraud_measures_desc': 'Your identity is encrypted. AI checks for duplicate or fake reports.',
        'describe_complaint_placeholder': 'Provide detailed information about the issue...',
        'complaint_hint': 'Detailed descriptions help our AI categorize your case faster.',
        'complaint_location': 'Pinpoint Location',
        'enter_exact_location': 'Enter exact landmark or street name',
        'location_hint': 'Accurate location helps field officers reach the spot quickly.',
        'upload_evidence': 'Upload Evidence',
        'drag_drop': 'Drag and drop or click to upload',
        'image_limits': 'Max 5 MB per image. Only JPG, PNG allowed.',
        'grievance_submission_success': 'Grievance submitted successfully!',
        'triage_details': 'Triage Details',
        'ai_analysis': 'AI Analysis',
        'officer_assignment': 'Officer Assignment',
    },
    
    hi: {
        // Common
        'app_name': 'स्मार्ट शिकायत प्रणाली',
        'welcome': 'स्वागत है',
        'logout': 'लॉग आउट',
        'submit': 'जमा करें',
        'cancel': 'रद्द करें',
        'save': 'सहेजें',
        'edit': 'संपादित करें',
        'delete': 'हटाएं',
        'view': 'देखें',
        'update': 'अपडेट करें',
        'back': 'वापस',
        'next': 'अगला',
        'previous': 'पिछला',
        'loading': 'लोड हो रहा है...',
        'success': 'सफलता',
        'error': 'त्रुटि',
        'warning': 'चेतावनी',
        'profile_btn': '👤 प्रोफाइल',
        'back_to_dashboard': 'डैशबोर्ड पर वापस जाएं',
        'back_to_login': 'लॉगिन पर वापस जाएं',
        
        // Auth
        'login': 'लॉगिन',
        'register': 'पंजीकरण',
        'email': 'ईमेल',
        'password': 'पासवर्ड',
        'name': 'नाम',
        'phone': 'फोन नंबर',
        'login_title': 'अपने खाते में लॉगिन करें',
        'register_title': 'नया खाता बनाएं',
        'forgot_password': 'पासवर्ड भूल गए?',
        'dont_have_account': 'खाता नहीं है?',
        'already_have_account': 'पहले से खाता है?',
        'verify_email_heading': 'अपना ईमेल सत्यापित करें',
        'enter_verification_code': '6-अंकीय सत्यापन कोड दर्ज करें',
        'resend_code': 'कोड पुन: भेजें',
        'reset_password': 'पासवर्ड रीसेट करें',
        'new_password': 'नया पासवर्ड',
        'confirm_password': 'नए पासवर्ड की पुष्टि करें',
        'complete_profile': 'अपनी प्रोफ़ाइल पूरी करें',
        'complete_profile_desc': 'कृपया अपनी प्रोफ़ाइल पूरी करने के लिए अपनी अधूरी जानकारी जोड़ें। शिकायतों को जमा करने के लिए यह आवश्यक है।',
        'update_now': 'अभी अपडेट करें',
        
        // Dashboard
        'dashboard': 'डैशबोर्ड',
        'my_grievances': 'मेरी शिकायतें',
        'submit_grievance': 'शिकायत दर्ज करें',
        'track_grievance': 'शिकायत ट्रैक करें',
        'profile': 'प्रोफ़ाइल',
        'total_complaints': 'कुल शिकायतें',
        'resolved': 'हल की गई',
        'pending': 'लंबित',
        'resolution_rate': 'समाधान दर',
        'public_dashboard_title': 'स्मार्ट शिकायत प्रणाली - सार्वजनिक डैशबोर्ड',
        'transparent_stats': 'पारदर्शी शिकायत आंकड़े',
        'realtime_data_desc': 'रीयल-टाइम संकलित डेटा। लॉगिन की आवश्यकता नहीं है।',
        'by_department': 'विभाग द्वारा',
        'dept_breakdown': 'विभाग-वार विवरण',
        'hero_title': 'नागरिकों को सशक्त बनाना, जवाबदेही सुनिश्चित करना',
        'hero_subtitle': 'बेहतर कल के लिए तेज़, पारदर्शी और एमएल-सहायता प्राप्त शिकायत निवारण।',
        'file_complaint': 'शिकायत दर्ज करें',
        'track_status': 'स्थिति ट्रैक करें',
        'resolved_cases': 'हल किए गए मामले',
        'public_stats': 'आंकड़े देखें',
        
        // Grievance
        'complaint_text': 'अपनी शिकायत का विवरण दें',
        'location': 'स्थान',
        'department': 'विभाग',
        'status': 'स्थिति',
        'submitted': 'जमा किया गया',
        'submitted_on': 'जमा करने की तिथि',
        'grievance_id': 'शिकायत आईडी',
        'complaint_details': 'शिकायत विवरण',
        'no_grievances': 'अभी तक कोई शिकायत जमा नहीं की गई है।',
        'no_resolved_cases': 'अभी तक कोई हल किए गए मामले उपलब्ध नहीं हैं।',
        'load_error': 'अभी डेटा लोड करने में असमर्थ।',
        'no_updates': 'अभी तक कोई अपडेट नहीं।',
        'no_comments': 'अभी तक कोई टिप्पणी नहीं।',
        'original_message': 'मूल संदेश',
        'original_text': 'मूल पाठ',
        'updated_by_label': 'द्वारा अपडेट किया गया',
        'translate_comment': '🌐 इस टिप्पणी का अनुवाद करें...',
        
        // Status keys
        'status_received': 'प्राप्त',
        'status_assigned': 'विभाग को सौंपा गया',
        'status_manual_review': 'मैनुअल समीक्षा आवश्यक',
        'status_under_progress': 'प्रगति में',
        'status_investigation': 'जांच',
        'status_reviewed': 'समीक्षा की गई',
        'status_resolved': 'हल हो गया',
        'status_closed': 'बंद',
        
        // Form specific
        'mandatory': 'अनिवार्य',
        'optional': 'वैकल्पिक',
        'mandatory_image_hint': 'इस शिकायत प्रकार के लिए कम से कम 1 छवि अनिवार्य है।',
        'optional_image_hint': 'छवियां वैकल्पिक हैं, लेकिन तेज़ सत्यापन के लिए सहायक हैं।',
        'listening_msg': 'सुन रहे हैं... अपनी शिकायत बोलें।',
        'use_gps': '📍 जीपीएस का उपयोग करें',
        'getting_location': 'स्थान प्राप्त कर रहे हैं...',
        
        // Officer/Admin Specific
        'officer_dashboard': 'अधिकारी डैशबोर्ड',
        'admin_dashboard': 'एडमिन डैशबोर्ड',
        'dept_grievances': 'विभाग की शिकायतें',
        'update_grievance': 'शिकायत अपडेट करें',
        'select_status': 'स्थिति चुनें',
        'under_progress': 'प्रगति में',
        'investigation': 'जांच',
        'update_message': 'अपडेट संदेश',
        'update_details_placeholder': 'इस अपडेट के बारे में विवरण प्रदान करें',
        'submit_update': 'अपडेट सबमिट करें',
        'comments_and_feedback': 'टिप्पणियाँ और प्रतिक्रिया',
        'add_comment': 'टिप्पणी जोड़ें',
        'post_comment': 'टिप्पणी पोस्ट करें',
        'type_comment_placeholder': 'अपनी प्रतिक्रिया या फीडबैक टाइप करें...',
        'system_analytics': 'सिस्टम एनालिटिक्स',
        'export_excel': '📊 एक्सेल में एक्सपोर्ट करें',
        'create_new_officer': '👤 नया अधिकारी बनाएं',
        'all_users_citizens': 'सभी उपयोगकर्ता/नागरिक',
        'all_officers': 'सभी अधिकारी',
        'apply_filters': 'फ़िल्टर लागू करें',
        'dept_info': '🏛️ विभाग की जानकारी',
        'designation': 'पद',
        'office_building': 'कार्यालय भवन',
        'responsibilities': 'जिम्मेदारियां',
        'office_contact_info': '📞 कार्यालय संपर्क जानकारी',
        'office_phone': 'कार्यालय फोन',
        'office_email': 'कार्यालय ईमेल',
        'personal_information': '📋 व्यक्तिगत जानकारी',
        'full_name': 'पूरा नाम',
        'residential_address_heading': '🏠 आवासीय पता',
        'address_line': 'पता',
        'city': 'शहर',
        'state': 'राज्य',
        'pincode': 'पिनकोड',
        'account_details': '🛡️ खाता विवरण',
        'member_since': 'सदस्यता तिथि',
        'verified': 'सत्यापित',
        'unverified': 'असत्यापित',
        'update_btn': 'प्रोफ़ाइल अपडेट करें',
        'save_changes': 'परिवर्तन सहेजें',
        
        // Auth Extended
        'secure_login_portal': 'सुरक्षित लॉगिन पोर्टल',
        'email_address': 'ईमेल पता',
        'enter_email': 'अपना ईमेल दर्ज करें',
        'enter_password': 'अपना पासवर्ड दर्ज करें',
        'register_here': 'यहां पंजीकरण करें',
        'view_public_statistics': '📊 सार्वजनिक आंकड़े देखें',
        'join_system': 'स्मार्ट शिकायत प्रणाली में शामिल हों',
        'first_name': 'पहला नाम',
        'enter_first_name': 'पहला नाम',
        'last_name': 'अंतिम नाम',
        'enter_last_name': 'अंतिम नाम',
        'phone_number': 'फ़ोन नंबर',
        'enter_phone': '10-अंकीय मोबाइल नंबर',
        'verified_via_otp': 'ओटीपी के माध्यम से सत्यापित किया जाएगा',
        'date_of_birth': 'जन्म तिथि',
        'must_be_18': 'पंजीकरण करने के लिए आपकी आयु 18 वर्ष या उससे अधिक होनी चाहिए',
        'gender': 'लिंग',
        'select_gender': '-- लिंग चुनें --',
        'male': 'पुरूष',
        'female': 'महिला',
        'other_gender': 'अन्य',
        'prefer_not_to_say': 'बताना नहीं चाहते',
        'accepted_gender_values': 'स्वीकृत मान: पुरुष, महिला, अन्य, बताना नहीं चाहते',
        'create_password': 'एक मजबूत पासवर्ड बनाएं',
        'password_requirements': 'बड़े अक्षरों, छोटे अक्षरों और नंबर के साथ न्यूनतम 8 वर्ण',
        'reenter_password': 'पासवर्ड पुनः दर्ज करें',
        'aadhaar_optional': 'आधार अंतिम 4 अंक (वैकल्पिक)',
        'last_4_digits': 'अंतिम 4 अंक',
        'data_consent': 'मैं अपने डेटा के प्रसंस्करण के लिए सहमति देता हूं',
        'login_here': 'यहां लॉगिन करें',
        'view_public_stats': 'आंकड़े देखें',
        
        // Dashboards Extended
        'welcome_hero': 'नागरिकों को सशक्त बनाना, जवाबदेही सुनिश्चित करना',
        'hero_description': 'बेहतर कल के लिए तेज़, पारदर्शी और एमएल-सहायता प्राप्त शिकायत निवारण।',
        'total_grievances': 'कुल शिकायतें',
        'in_progress': 'प्रगति में',
        'avg_resolution': 'औसत समाधान समय',
        'recently_resolved_cases': 'हाल ही में हल किए गए मामले',
        'resolved_cases_desc': 'कार्यवाही में पारदर्शिता: नवीनतम हल की गई शिकायतें।',
        'submit_new_grievance': 'नई शिकायत दर्ज करें',
        'view_all': 'सभी देखें',
        'department_metrics': 'विभाग मेट्रिक्स',
        'fraud_alert_system': 'धोखाधड़ी चेतावनी प्रणाली',
        'all_statuses': 'सभी स्थितियाँ',
        'all_departments': 'सभी विभाग',
        'search': 'खोजें',
        'download_report': 'रिपोर्ट डाउनलोड करें',
        'select_department': 'विभाग का चयन करें',
        'password_hint': '8+ वर्ण, बड़े अक्षर, छोटे अक्षर और नंबर के साथ',
        'address_required': 'पूरा पता',
        'address_required_desc': 'स्थल सत्यापन के लिए पूरा पता प्रदान करें',
        'anti_fraud_measures': 'धोखाधड़ी विरोधी सुरक्षा',
        'anti_fraud_measures_desc': 'आपकी पहचान एन्क्रिप्टेड है। एआई डुप्लिकेट या फर्जी रिपोर्ट की जांच करता है।',
        'describe_complaint_placeholder': 'मुद्दे के बारे में विस्तृत जानकारी प्रदान करें...',
        'complaint_hint': 'विस्तृत विवरण हमारे एआई को आपके मामले को तेजी से वर्गीकृत करने में मदद करते हैं।',
        'complaint_location': 'सटीक स्थान',
        'enter_exact_location': 'सटीक लैंडमार्क या सड़क का नाम दर्ज करें',
        'location_hint': 'सटीक स्थान फील्ड अधिकारियों को जल्दी पहुंचने में मदद करता है।',
        'upload_evidence': 'प्रमाण अपलोड करें',
        'drag_drop': 'अपलोड करने के लिए खींचें और छोड़ें या क्लिक करें',
        'image_limits': 'प्रति छवि अधिकतम 5 एमबी। केवल जेपीजी, पीएनजी की अनुमति है।',
        'grievance_submission_success': 'शिकायत सफलतापूर्वक जमा की गई!',
        'triage_details': 'ट्राइएज विवरण',
        'ai_analysis': 'एआई विश्लेषण',
        'officer_assignment': 'अधिकारी नियुक्ति',
    },
    
    ta: {
        // Common
        'app_name': 'ஸ்மார்ட் குறைதீர்ப்பு அமைப்பு',
        'welcome': 'வரவேற்கிறோம்',
        'logout': 'வெளியேறு',
        'submit': 'சமர்ப்பிக்கவும்',
        'cancel': 'ரத்து செய்',
        'save': 'சேமி',
        'edit': 'திருத்து',
        'delete': 'நீக்கு',
        'view': 'பார்க்க',
        'update': 'புதுப்பிக்கவும்',
        'back': 'பின்',
        'next': 'அடுத்து',
        'previous': 'முந்தைய',
        'loading': 'ஏற்றுகிறது...',
        'success': 'வெற்றி',
        'error': 'பிழை',
        'warning': 'எச்சரிக்கை',
        'profile_btn': '👤 சுயவிவரம்',
        'back_to_dashboard': 'டாஷ்போர்டுக்குத் திரும்பு',
        
        // Auth
        'login': 'உள்நுழைய',
        'register': 'பதிவு செய்க',
        'email': 'மின்னஞ்சல்',
        'password': 'கடவுச்சொல்',
        'login_title': 'உங்கள் கணக்கில் உள்நுழைக',
        'register_title': 'புதிய கணக்கை உருவாக்கவும்',
        'forgot_password': 'கடவுச்சொல்லை மறந்துவிட்டீர்களா?',
        'dont_have_account': 'கணக்கு இல்லையா?',
        'already_have_account': 'ஏற்கனவே கணக்கு உள்ளதா?',
        'verify_email_heading': 'மின்னஞ்சலைச் சரிபார்க்கவும்',
        'enter_verification_code': '6-இலக்க சரிபார்ப்புக் குறியீட்டை உள்ளிடவும்',
        'resend_code': 'குறியீட்டை மீண்டும் அனுப்பவும்',
        'reset_password': 'கடவுச்சொல்லை மீட்டமைக்கவும்',
        'complete_profile': 'சுயவிவரத்தை பூர்த்தி செய்யவும்',
        'complete_profile_desc': 'உங்கள் சுயவிவரத்தை பூர்த்தி செய்ய விடுபட்ட தகவல்களைச் சேர்க்கவும். புகார்களைச் சமர்ப்பிக்க இது அவசியம்.',
        'update_now': 'இப்போது புதுப்பிக்கவும்',
        
        // Dashboard
        'dashboard': 'டாஷ்போர்டு',
        'my_grievances': 'எனது குறைகள்',
        'submit_grievance': 'குறை சமர்ப்பிக்கவும்',
        'track_grievance': 'குறையைக் கண்காணிக்கவும்',
        'profile': 'சுயவிவரம்',
        'total_complaints': 'மொத்த புகார்கள்',
        'resolved': 'தீர்வு காணப்பட்டது',
        'pending': 'நிலுவையில் உள்ளது',
        'resolution_rate': 'தீர்வு விகிதம்',
        'public_dashboard_title': 'ஸ்மார்ட் குறைதீர்ப்பு அமைப்பு - பொது டாஷ்போர்டு',
        'transparent_stats': 'வெளிப்படையான புகார் புள்ளிவிவரங்கள்',
        'realtime_data_desc': 'நிகழ்நேரத் தரவு. உள்நுழைவு தேவையில்லை.',
        'by_department': 'துறை வாரியாக',
        'dept_breakdown': 'துறை வாரியான விவரங்கள்',
        'file_complaint': 'புகார் சமர்ப்பிக்கவும்',
        'track_status': 'நிலையை அறிய',
        'resolved_cases': 'தீர்வு காணப்பட்ட வழக்குகள்',
        
        // Grievance
        'complaint_text': 'உங்கள் புகாரை விவரிக்கவும்',
        'location': 'இடம்',
        'department': 'துறை',
        'status': 'நிலை',
        'submitted': 'சமர்ப்பிக்கப்பட்டது',
        'submitted_on': 'சமர்ப்பிக்கப்பட்ட தேதி',
        'grievance_id': 'குறை ஐடி',
        'complaint_details': 'புகார் விவரங்கள்',
        'no_grievances': 'இன்னும் புகார்கள் எதுவும் சமர்ப்பிக்கப்படவில்லை.',
        'no_resolved_cases': 'இன்னும் தீர்வு காணப்பட்ட வழக்குகள் எதுவும் இல்லை.',
        'no_updates': 'இன்னும் புதுப்பிப்புகள் இல்லை.',
        'original_message': 'அசல் செய்தி',
        'original_text': 'அசல் உரை',
        'updated_by_label': 'புதுப்பித்தவர்',
        'translate_comment': '🌐 இந்தக் கருத்தை மொழிபெயர்க்கவும்...',
        
        // Status keys
        'status_received': 'பெறப்பட்டது',
        'status_assigned': 'துறைக்கு ஒதுக்கப்பட்டது',
        'status_manual_review': 'கைமுறை மதிப்பாய்வு தேவை',
        'status_under_progress': 'செயல்பாட்டில் உள்ளது',
        'status_investigation': 'விசாரணையில்',
        'status_reviewed': 'மதிப்பாய்வு செய்யப்பட்டது',
        'status_resolved': 'தீர்வு காணப்பட்டது',
        'status_closed': 'மூடப்பட்டது',
        
        // Form specific
        'mandatory': 'கட்டாயமானது',
        'optional': 'விருப்பத்திற்குரியது',
        'mandatory_image_hint': 'இந்த வகை புகாருக்கு குறைந்தது 1 படம் கட்டாயமாகும்.',
        'optional_image_hint': 'படங்கள் கட்டாயமில்லை, ஆனால் விரைவான சரிபார்ப்புக்கு உதவும்.',
        'listening_msg': 'கேட்டுக்கொண்டிருக்கிறோம்... உங்கள் புகாரைக் கூறவும்.',
        'use_gps': '📍 ஜிபிஎஸ் பயன்படுத்தவும்',
        'getting_location': 'இடத்தைப் பெறுகிறது...',
        
        // Officer/Admin Specific
        'officer_dashboard': 'அதிகாரி டாஷ்போர்டு',
        'admin_dashboard': 'நிர்வாக டாஷ்போர்டு',
        'dept_grievances': 'துறை புகார்கள்',
        'update_grievance': 'புகாரைப் புதுப்பிக்கவும்',
        'select_status': 'நிலையைத் தேர்ந்தெடு',
        'update_message': 'புதுப்பிப்புச் செய்தி',
        'submit_update': 'புதுப்பிப்பைச் சமர்ப்பிக்கவும்',
        'comments_and_feedback': 'கருத்துகள் மற்றும் பின்னூட்டம்',
        'add_comment': 'கருத்தைச் சேர்க்கவும்',
        'post_comment': 'கருத்தைப் பதிவிடவும்',
        'system_analytics': 'அமைப்பு புள்ளிவிவரங்கள்',
        'personal_information': '📋 தனிப்பட்ட தகவல்கள்',
        'full_name': 'முழு பெயர்',
        'residential_address_heading': '🏠 குடியிருப்பு முகவரி',
        'city': 'நகரம்',
        'state': 'மாநிலம்',
        'pincode': 'அஞ்சல் குறியீடு',
        'verified': 'சரிபார்க்கப்பட்டது',
        'update_btn': 'சுயவிவரத்தைப் புதுப்பிக்கவும்',
        
        // Auth Extended
        'secure_login_portal': 'பாதுகாப்பான உள்நுழைவு போர்டல்',
        'email_address': 'மின்னஞ்சல் முகவரி',
        'enter_email': 'உங்கள் மின்னஞ்சலை உள்ளிடவும்',
        'enter_password': 'உங்கள் கடவுச்சொல்லை உள்ளிடவும்',
        'register_here': 'இங்கே பதிவு செய்யுங்கள்',
        'view_public_statistics': '📊 பொது புள்ளிவிவரங்களைக் காண்க',
        'join_system': 'ஸ்மார்ட் குறை தீர்க்கும் அமைப்பில் சேரவும்',
        'first_name': 'முதல் பெயர்',
        'enter_first_name': 'முதல் பெயர்',
        'last_name': 'பரிதி பெயர்',
        'enter_last_name': 'பரிதி பெயர்',
        'phone_number': 'தொலைபேసి எண்',
        'enter_phone': '10 இலக்க மொபைல் எண்',
        'verified_via_otp': 'OTP மூலம் சரிபார்க்கப்படும்',
        'date_of_birth': 'பிறந்த தேதி',
        'must_be_18': 'பதிவு செய்ய நீங்கள் 18 வயது அல்லது அதற்கு மேல் இருக்க வேண்டும்',
        'gender': 'பாலினம்',
        'select_gender': '-- பாலினத்தைத் தேர்வுசெய்க --',
        'male': 'ஆண்',
        'female': 'பெண்',
        'other_gender': 'மற்றவை',
        'prefer_not_to_say': 'சொல்ல விரும்பவில்லை',
        'accepted_gender_values': 'ஏற்றுக்கொள்ளப்பட்ட மதிப்புகள்: ஆண், பெண், மற்றவை, சொல்ல விரும்பவில்லை',
        'create_password': 'வலுவான கடவுச்சொல்லை உருவாக்கவும்',
        'password_requirements': 'பெரிய எழுத்துக்கள், சிறிய எழுத்துக்கள் மற்றும் எண்ணுடன் குறைந்தபட்சம் 8 எழுத்துக்கள்',
        'reenter_password': 'கடவுச்சொல்லை மீண்டும் உள்ளிடவும்',
        'aadhaar_optional': 'ஆதார் கடைசி 4 இலக்கங்கள் (விருப்பமானது)',
        'last_4_digits': 'கடைசி 4 இலக்கங்கள்',
        'data_consent': 'எனது தரவை செயலாக்க நான் ஒப்புக்கொள்கிறேன்',
        'login_here': 'இங்கே உள்நுழையவும்',
        'view_public_stats': 'புள்ளிவிவரங்களைக் காண்க',
        
        // Dashboards Extended
        'welcome_hero': 'குடிமக்களுக்கு அதிகாரம் அளித்தல், பொறுப்புணர்வை உறுதி செய்தல்',
        'hero_description': 'சிறந்த நாளைக்காக விரைவான, வெளிப்படையான மற்றும் ML-உதவியுடன் கூடிய குறை தீர்க்கும் முறை.',
        'total_grievances': 'மொத்த புகார்கள்',
        'in_progress': 'செயல்பாட்டில் உள்ளது',
        'avg_resolution': 'சராசரி தீர்வு நேரம்',
        'recently_resolved_cases': 'சமீபத்தில் தீர்க்கப்பட்ட வழக்குகள்',
        'resolved_cases_desc': 'செயல்பாட்டில் வெளிப்படைத்தன்மை: சமீபத்திய தீர்க்கப்பட்ட குறைகள்.',
        'submit_new_grievance': 'புதிய புகாரைச் சமர்ப்பிக்கவும்',
        'view_all': 'அனைத்தையும் காண்க',
        'department_metrics': 'துறை அளவீடுகள்',
        'fraud_alert_system': 'மோசடி எச்சரிக்கை அமைப்பு',
        'all_statuses': 'அனைத்து நிலைகளும்',
        'all_departments': 'அனைத்து துறைகளும்',
        'search': 'தேடல்',
        'download_report': 'அறிக்கையைப் பதிவிறக்கவும்',
        'select_department': 'துறையைத் தேர்ந்தெடுக்கவும்',
        'password_hint': '8+ எழுத்துக்கள், பெரிய எழுத்துக்கள், சிறிய எழுத்துக்கள் மற்றும் எண்களுடன்',
        'address_required': 'முழு முகவரி',
        'address_required_desc': 'தள சரிபார்ப்பிற்கு முழு முகவரியை வழங்கவும்',
        'anti_fraud_measures': 'மோசடி எதிர்ப்பு பாதுகாப்பு',
        'anti_fraud_measures_desc': 'உங்கள் அடையாளம் குறியாக்கம் செய்யப்பட்டுள்ளது. போலி அறிக்கைகளை AI சரிபார்க்கிறது.',
        'describe_complaint_placeholder': 'பிரச்சனை பற்றிய விரிவான தகவல்களை வழங்கவும்...',
        'complaint_hint': 'விரிவான விளக்கங்கள் உங்கள் வழக்கை விரைவாக வகைப்படுத்த உதவுகின்றன.',
        'complaint_location': 'துல்லியமான இடம்',
        'enter_exact_location': 'துல்லியமான அடையாளக் குறி அல்லது தெருப் பெயரை உள்ளிடவும்',
        'location_hint': 'துல்லியமான இடம் கள அதிகாரிகள் விரைவாக வந்தடைய உதவுகிறது.',
        'upload_evidence': 'ஆதாரங்களை பதிவேற்றவும்',
        'drag_drop': 'பதிவேற்ற இழுத்து விடவும் அல்லது கிளிக் செய்யவும்',
        'image_limits': 'ஒவ்வொரு படத்திற்கும் அதிகபட்சம் 5 MB. JPG, PNG மட்டுமே அனுமதிக்கப்படும்.',
        'grievance_submission_success': 'குறை வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது!',
        'triage_details': 'ட்ரைஏஜ் விவரங்கள்',
        'ai_analysis': 'AI பகுப்பாய்வு',
        'officer_assignment': 'அதிகாரி ஒதுக்கீடு',
    },
    
    te: {
        // Common
        'app_name': 'స్మార్ట్ ఫిర్యాదు వ్యవస్థ',
        'welcome': 'స్వాగతం',
        'logout': 'లాగౌట్',
        'submit': 'సమర్పించండి',
        'cancel': 'రద్దు చేయి',
        'save': 'సేవ్ చేయి',
        'edit': 'సవరించు',
        'view': 'చూడండి',
        'update': 'నవీకరించు',
        'back': 'వెనుకకు',
        
        // Auth
        'login': 'లాగిన్',
        'register': 'నమోదు',
        'email': 'ఇమెయిల్',
        'password': 'పాస్‌వర్డ్',
        'name': 'పేరు',
        'phone': 'ఫోన్ నంబర్',
        
        // Dashboard
        'dashboard': 'డాష్‌బోర్డ్',
        'my_grievances': 'నా ఫిర్యాదులు',
        'submit_grievance': 'ఫిర్యాదు సమర్పించండి',
        'profile': 'ప్రొఫైల్',
        
        // Language
        'change_language': 'భాషను మార్చండి',
        'select_language': 'భాషను ఎంచుకోండి'
    },
    
    bn: {
        // Common
        'app_name': 'স্মার্ট অভিযোগ সিস্টেম',
        'welcome': 'স্বাগতম',
        'logout': 'লগআউট',
        'submit': 'জমা দিন',
        'cancel': 'বাতিল',
        'save': 'সংরক্ষণ',
        'edit': 'সম্পাদনা',
        'view': 'দেখুন',
        'update': 'আপডেট',
        'back': 'পিছনে',
        
        // Auth
        'login': 'লগইন',
        'register': 'নিবন্ধন',
        'email': 'ইমেইল',
        'password': 'পাসওয়ার্ড',
        'name': 'নাম',
        'phone': 'ফোন নম্বর',
        
        // Dashboard
        'dashboard': 'ড্যাশবোর্ড',
        'my_grievances': 'আমার অভিযোগ',
        'submit_grievance': 'অভিযোগ জমা দিন',
        'profile': 'প্রোফাইল',
        
        // Language
        'change_language': 'ভাষা পরিবর্তন করুন',
        'select_language': 'ভাষা নির্বাচন করুন'
    },
    
    mr: {
        // Common
        'app_name': 'स्मार्ट तक्रार प्रणाली',
        'welcome': 'स्वागत आहे',
        'logout': 'लॉगआउट',
        'submit': 'सबमिट करा',
        'cancel': 'रद्द करा',
        'save': 'जतन करा',
        'edit': 'संपादित करा',
        'view': 'पहा',
        'update': 'अपडेट करा',
        
        // Auth
        'login': 'लॉगिन',
        'register': 'नोंदणी',
        'email': 'ईमेल',
        'password': 'पासवर्ड',
        'name': 'नाव',
        'phone': 'फोन नंबर',
        
        // Dashboard
        'dashboard': 'डॅशबोर्ड',
        'my_grievances': 'माझ्या तक्रारी',
        'submit_grievance': 'तक्रार सबमिट करा',
        'profile': 'प्रोफाइल',
        
        // Language
        'change_language': 'भाषा बदला',
        'select_language': 'भाषा निवडा'
    },
    
    gu: {
        // Common
        'app_name': 'સ્માર્ટ ફરિયાદ સિસ્ટમ',
        'welcome': 'સ્વાગત છે',
        'logout': 'લૉગઆઉટ',
        'submit': 'સબમિટ કરો',
        'cancel': 'રદ કરો',
        'save': 'સાચવો',
        'edit': 'સંપાદિત કરો',
        'view': 'જુઓ',
        'update': 'અપડેટ કરો',
        
        // Auth
        'login': 'લૉગિન',
        'register': 'નોંધણી',
        'email': 'ઈમેલ',
        'password': 'પાસવર્ડ',
        'name': 'નામ',
        'phone': 'ફોન નંબર',
        
        // Dashboard
        'dashboard': 'ડેશબોર્ડ',
        'my_grievances': 'મારી ફરિયાદો',
        'submit_grievance': 'ફરિયાદ સબમિટ કરો',
        'profile': 'પ્રોફાઇલ',
        
        // Language
        'change_language': 'ભાષા બદલો',
        'select_language': 'ભાષા પસંદ કરો'
    },
    
    kn: {
        // Common
        'app_name': 'ಸ್ಮಾರ್ಟ್ ದೂರು ವ್ಯವಸ್ಥೆ',
        'welcome': 'ಸ್ವಾಗತ',
        'logout': 'ಲಾಗ್ಔಟ್',
        'submit': 'ಸಲ್ಲಿಸಿ',
        'cancel': 'ರದ್ದುಮಾಡಿ',
        'save': 'ಉಳಿಸಿ',
        'edit': 'ಸಂಪಾದಿಸಿ',
        'view': 'ವೀಕ್ಷಿಸಿ',
        'update': 'ನವೀಕರಿಸಿ',
        
        // Auth
        'login': 'ಲಾಗಿನ್',
        'register': 'ನೋಂದಣಿ',
        'email': 'ಇಮೇಲ್',
        'password': 'ಪಾಸ್‌ವರ್ಡ್',
        'name': 'ಹೆಸರು',
        'phone': 'ಫೋನ್ ಸಂಖ್ಯೆ',
        
        // Dashboard
        'dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
        'my_grievances': 'ನನ್ನ ದೂರುಗಳು',
        'submit_grievance': 'ದೂರು ಸಲ್ಲಿಸಿ',
        'profile': 'ಪ್ರೊಫೈಲ್',
        
        // Language
        'change_language': 'ಭಾಷೆ ಬದಲಿಸಿ',
        'select_language': 'ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ'
    },
    
    ml: {
        // Common
        'app_name': 'സ്മാർട്ട് പരാതി സംവിധാനം',
        'welcome': 'സ്വാഗതം',
        'logout': 'ലോഗൗട്ട്',
        'submit': 'സമർപ്പിക്കുക',
        'cancel': 'റദ്ദാക്കുക',
        'save': 'സംരക്ഷിക്കുക',
        'edit': 'എഡിറ്റ് ചെയ്യുക',
        'view': 'കാണുക',
        'update': 'അപ്ഡേറ്റ് ചെയ്യുക',
        
        // Auth
        'login': 'ലോഗിൻ',
        'register': 'രജിസ്റ്റർ',
        'email': 'ഇമെയിൽ',
        'password': 'പാസ്‌വേഡ്',
        'name': 'പേര്',
        'phone': 'ഫോൺ നമ്പർ',
        
        // Dashboard
        'dashboard': 'ഡാഷ്‌ബോർഡ്',
        'my_grievances': 'എന്റെ പരാതികൾ',
        'submit_grievance': 'പരാതി സമർപ്പിക്കുക',
        'profile': 'പ്രൊഫൈൽ',
        
        // Language
        'change_language': 'ഭാഷ മാറ്റുക',
        'select_language': 'ഭാഷ തിരഞ്ഞെടുക്കുക'
    },
    
    pa: {
        // Common
        'app_name': 'ਸਮਾਰਟ ਸ਼ਿਕਾਇਤ ਪ੍ਰਣਾਲੀ',
        'welcome': 'ਸੁਆਗਤ ਹੈ',
        'logout': 'ਲਾਗਆਉਟ',
        'submit': 'ਜਮ੍ਹਾਂ ਕਰੋ',
        'cancel': 'ਰੱਦ ਕਰੋ',
        'save': 'ਸੁਰੱਖਿਅਤ ਕਰੋ',
        'edit': 'ਸੰਪਾਦਿਤ ਕਰੋ',
        'view': 'ਦੇਖੋ',
        'update': 'ਅੱਪਡੇਟ ਕਰੋ',
        
        // Auth
        'login': 'ਲਾਗਇਨ',
        'register': 'ਰਜਿਸਟਰ',
        'email': 'ਈਮੇਲ',
        'password': 'ਪਾਸਵਰਡ',
        'name': 'ਨਾਮ',
        'phone': 'ਫ਼ੋਨ ਨੰਬਰ',
        
        // Dashboard
        'dashboard': 'ਡੈਸ਼ਬੋਰਡ',
        'my_grievances': 'ਮੇਰੀਆਂ ਸ਼ਿਕਾਇਤਾਂ',
        'submit_grievance': 'ਸ਼ਿਕਾਇਤ ਜਮ੍ਹਾਂ ਕਰੋ',
        'profile': 'ਪ੍ਰੋਫਾਈਲ',
        
        // Language
        'change_language': 'ਭਾਸ਼ਾ ਬਦਲੋ',
        'select_language': 'ਭਾਸ਼ਾ ਚੁਣੋ'
    },
    
    or: {
        // Common
        'app_name': 'ସ୍ମାର୍ଟ ଅଭିଯୋଗ ବ୍ୟବସ୍ଥା',
        'welcome': 'ସ୍ୱାଗତ',
        'logout': 'ଲଗଆଉଟ୍',
        'submit': 'ଦାଖଲ କରନ୍ତୁ',
        'cancel': 'ବାତିଲ କରନ୍ତୁ',
        'save': 'ସଞ୍ଚୟ କରନ୍ତୁ',
        'edit': 'ସମ୍ପାଦନା କରନ୍ତୁ',
        'view': 'ଦେଖନ୍ତୁ',
        'update': 'ଅପଡେଟ୍ କରନ୍ତୁ',
        
        // Auth
        'login': 'ଲଗଇନ୍',
        'register': 'ପଞ୍ଜୀକରଣ',
        'email': 'ଇମେଲ୍',
        'password': 'ପାସୱାର୍ଡ',
        'name': 'ନାମ',
        'phone': 'ଫୋନ୍ ନମ୍ବର',
        
        // Dashboard
        'dashboard': 'ଡ୍ୟାସବୋର୍ଡ',
        'my_grievances': 'ମୋର ଅଭିଯୋଗ',
        'submit_grievance': 'ଅଭିଯୋଗ ଦାଖଲ କରନ୍ତୁ',
        'profile': 'ପ୍ରୋଫାଇଲ୍',
        
        // Language
        'change_language': 'ଭାଷା ପରିବର୍ତ୍ତନ କରନ୍ତୁ',
        'select_language': 'ଭାଷା ଚୟନ କରନ୍ତୁ'
    },
    
    ur: {
        // Common
        'app_name': 'سمارٹ شکایت نظام',
        'welcome': 'خوش آمدید',
        'logout': 'لاگ آؤٹ',
        'submit': 'جمع کرائیں',
        'cancel': 'منسوخ کریں',
        'save': 'محفوظ کریں',
        'edit': 'ترمیم کریں',
        'view': 'دیکھیں',
        'update': 'اپ ڈیٹ کریں',
        
        // Auth
        'login': 'لاگ ان',
        'register': 'رجسٹر',
        'email': 'ای میل',
        'password': 'پاس ورڈ',
        'name': 'نام',
        'phone': 'فون نمبر',
        
        // Dashboard
        'dashboard': 'ڈیش بورڈ',
        'my_grievances': 'میری شکایات',
        'submit_grievance': 'شکایت جمع کرائیں',
        'profile': 'پروفائل',
        
        // Language
        'change_language': 'زبان تبدیل کریں',
        'select_language': 'زبان منتخب کریں'
    }
};

// Translation helper function
function translate(key, lang = null) {
    const currentLang = lang || localStorage.getItem('selectedLanguage') || localStorage.getItem('preferredLanguage') || 'en';
    if (translations[currentLang] && translations[currentLang][key]) return translations[currentLang][key];
    if (translations['en'] && translations['en'][key]) return translations['en'][key];
    
    // Log missing translation for production debugging
    console.warn(`[i18n missing] ${key} (Lang: ${currentLang})`);
    
    // Auto-format missing translation keys to look natural (e.g., 'app_name' -> 'App Name')
    if (typeof key === 'string') {
        return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }
    return key;
}

// Apply translations to page
function applyTranslations() {
    const currentLang = localStorage.getItem('selectedLanguage') || localStorage.getItem('preferredLanguage') || 'en';
    
    // Translate elements with data-translate attribute
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        const translation = translate(key, currentLang);
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            element.placeholder = translation;
        } else {
            element.textContent = translation;
        }
    });
}

// Language switcher component
function createLanguageSwitcher() {
    const currentLang = localStorage.getItem('preferredLanguage') || 'en';
    const languages = (typeof getPortalLanguages === 'function')
        ? getPortalLanguages().map((lang) => ({
            code: lang.code,
            name: lang.nativeName,
            flag: lang.flag || '🌐'
        }))
        : [
            { code: 'en', name: 'English', flag: '🇬🇧' },
            { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
            { code: 'bn', name: 'বাংলা', flag: '🇮🇳' },
            { code: 'ta', name: 'தமிழ்', flag: '🇮🇳' },
            { code: 'te', name: 'తెలుగు', flag: '🇮🇳' },
            { code: 'mr', name: 'मराठी', flag: '🇮🇳' },
            { code: 'gu', name: 'ગુજરાતી', flag: '🇮🇳' },
            { code: 'kn', name: 'ಕನ್ನಡ', flag: '🇮🇳' },
            { code: 'ml', name: 'മലയാളം', flag: '🇮🇳' },
            { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
            { code: 'or', name: 'ଓଡ଼ିଆ', flag: '🇮🇳' },
            { code: 'ur', name: 'اردو', flag: '🇮🇳' }
        ];
    
    const currentLangObj = languages.find(l => l.code === currentLang) || languages[0];
    
    return `
        <div class="language-switcher" style="position: relative; display: inline-block;">
            <button class="language-btn" onclick="toggleLanguageMenu()" style="
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            ">
                <span>${currentLangObj.flag}</span>
                <span>${currentLangObj.name}</span>
                <span style="font-size: 0.7rem;">▼</span>
            </button>
            <div id="languageMenu" class="language-menu" style="
                display: none;
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 8px;
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                z-index: 1000;
                min-width: 200px;
                max-height: 400px;
                overflow-y: auto;
            ">
                ${languages.map(lang => `
                    <div class="language-option" onclick="changeLanguage('${lang.code}')" style="
                        padding: 12px 16px;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        transition: background 0.2s ease;
                        ${lang.code === currentLang ? 'background: rgba(255, 153, 51, 0.1);' : ''}
                    " onmouseover="this.style.background='rgba(255, 153, 51, 0.05)'" onmouseout="this.style.background='${lang.code === currentLang ? 'rgba(255, 153, 51, 0.1)' : 'white'}'">
                        <span style="font-size: 1.5rem;">${lang.flag}</span>
                        <span style="font-weight: ${lang.code === currentLang ? '600' : '400'};">${lang.name}</span>
                        ${lang.code === currentLang ? '<span style="margin-left: auto; color: #FF9933;">✓</span>' : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function toggleLanguageMenu() {
    const menu = document.getElementById('languageMenu');
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

function changeLanguage(code) {
    localStorage.setItem('preferredLanguage', code);
    window.location.reload();
}

// Close language menu when clicking outside
document.addEventListener('click', (e) => {
    const languageSwitcher = document.querySelector('.language-switcher');
    if (languageSwitcher && !languageSwitcher.contains(e.target)) {
        const menu = document.getElementById('languageMenu');
        if (menu) menu.style.display = 'none';
    }
});

// Auto-apply translations on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyTranslations);
} else {
    applyTranslations();
}
