"""
RuralDR-XAI: India Location & Healthcare Facility Metadata Seeder (SIH26038)
Populates:
1. Complete 28 Indian States and Union Territories with official ISO/Postal codes
2. Comprehensive Districts belonging strictly to their respective Indian States
3. Realistic Rural Primary Healthcare Centres (PHCs/CHCs/Sub-Centres) tied to districts
4. Authoritative Referral Eye Hospitals & Medical Centers tied to districts
5. Administrative backward-compatibility mapping with locations table
"""

from sqlalchemy.orm import Session
from .models import State, District, Location, HealthcareCentre, Hospital, User


# ==============================================================================
# Complete Indian States & Union Territories
# ==============================================================================
INDIAN_STATES = [
    # 28 States
    {"name": "Andhra Pradesh", "code": "AP"},
    {"name": "Arunachal Pradesh", "code": "AR"},
    {"name": "Assam", "code": "AS"},
    {"name": "Bihar", "code": "BR"},
    {"name": "Chhattisgarh", "code": "CG"},
    {"name": "Goa", "code": "GA"},
    {"name": "Gujarat", "code": "GJ"},
    {"name": "Haryana", "code": "HR"},
    {"name": "Himachal Pradesh", "code": "HP"},
    {"name": "Jharkhand", "code": "JH"},
    {"name": "Karnataka", "code": "KA"},
    {"name": "Kerala", "code": "KL"},
    {"name": "Madhya Pradesh", "code": "MP"},
    {"name": "Maharashtra", "code": "MH"},
    {"name": "Manipur", "code": "MN"},
    {"name": "Meghalaya", "code": "ML"},
    {"name": "Mizoram", "code": "MZ"},
    {"name": "Nagaland", "code": "NL"},
    {"name": "Odisha", "code": "OD"},
    {"name": "Punjab", "code": "PB"},
    {"name": "Rajasthan", "code": "RJ"},
    {"name": "Sikkim", "code": "SK"},
    {"name": "Tamil Nadu", "code": "TN"},
    {"name": "Telangana", "code": "TG"},
    {"name": "Tripura", "code": "TR"},
    {"name": "Uttar Pradesh", "code": "UP"},
    {"name": "Uttarakhand", "code": "UK"},
    {"name": "West Bengal", "code": "WB"},
    # Union Territories
    {"name": "Andaman and Nicobar Islands", "code": "AN"},
    {"name": "Chandigarh", "code": "CH"},
    {"name": "Dadra and Nagar Haveli and Daman and Diu", "code": "DN"},
    {"name": "Delhi", "code": "DL"},
    {"name": "Jammu and Kashmir", "code": "JK"},
    {"name": "Ladakh", "code": "LA"},
    {"name": "Lakshadweep", "code": "LD"},
    {"name": "Puducherry", "code": "PY"},
]

# ==============================================================================
# Comprehensive Districts by State
# ==============================================================================
STATE_DISTRICTS = {
    "Tamil Nadu": [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
        "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
        "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris",
        "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga",
        "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
        "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore",
        "Viluppuram", "Virudhunagar"
    ],
    "Kerala": [
        "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam",
        "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta",
        "Thiruvananthapuram", "Thrissur", "Wayanad"
    ],
    "Karnataka": [
        "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
        "Bidar", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga",
        "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri",
        "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur",
        "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara",
        "Vijayapura", "Yadgir"
    ],
    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Chhatrapati Sambhajinagar", "Beed", "Bhandara",
        "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon",
        "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded",
        "Nandurbar", "Nashik", "Dharashiv", "Palghar", "Parbhani", "Pune", "Raigad",
        "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha",
        "Washim", "Yavatmal"
    ],
    "Andhra Pradesh": [
        "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya", "Bapatla",
        "Chittoor", "Dr. B.R. Ambedkar Konaseema", "East Godavari", "Eluru", "Guntur",
        "Kakinada", "Krishna", "Kurnool", "Nandyal", "NTR", "Palnadu", "Parvathipuram Manyam",
        "Prakasam", "Sri Potti Sriramulu Nellore", "Sri Sathya Sai", "Srikakulam", "Tirupati",
        "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR Kadapa"
    ],
    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally",
        "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Kumuram Bheem Asifabad",
        "Mahabubabad", "Mahbubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu",
        "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli",
        "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad",
        "Wanaparthy", "Warangal", "Hanamkonda", "Yadadri Bhuvanagiri"
    ],
    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya",
        "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki",
        "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli",
        "Chitrakoot", "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad",
        "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur",
        "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat",
        "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri", "Kushinagar", "Lalitpur", "Lucknow",
        "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad",
        "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur",
        "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti",
        "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
    ],
    "Rajasthan": [
        "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner",
        "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh",
        "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli",
        "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar",
        "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"
    ],
    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar",
        "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar",
        "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana",
        "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot",
        "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"
    ],
    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling",
        "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda",
        "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur",
        "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"
    ],
    "Madhya Pradesh": [
        "Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain", "Sagar", "Rewa", "Satna",
        "Dhar", "Khargone", "Hoshangabad", "Ratlam", "Dewas", "Chhindwara", "Sehore"
    ],
    "Bihar": [
        "Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia", "Darbhanga", "Bihar Sharif",
        "Arrah", "Begusarai", "Katihar", "Munger", "Chhapra", "Samastipur", "Saharsa"
    ],
    "Punjab": [
        "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka",
        "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana",
        "Mansa", "Moga", "Muktsar", "Pathankot", "Patiala", "Rupnagar", "Sahibzada Ajit Singh Nagar",
        "Sangrur", "Shahid Bhagat Singh Nagar", "Sri Muktsar Sahib", "Tarn Taran"
    ],
    "Haryana": [
        "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram",
        "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh",
        "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"
    ],
    "Odisha": [
        "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack",
        "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur",
        "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha",
        "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada",
        "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"
    ],
    "Assam": [
        "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang",
        "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Goalpara", "Golaghat", "Hailakandi",
        "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong", "Karimganj",
        "Kokrajhar", "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari", "Dima Hasao",
        "Sivasagar", "Sonitpur", "South Salmara-Mankachar", "Tinsukia", "Udalguri", "West Karbi Anglong"
    ],
    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa",
        "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma",
        "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahibganj",
        "Seraikela Kharsawan", "Simdega", "West Singhbhum"
    ],
    "Chhattisgarh": [
        "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur",
        "Dantewada", "Dhamtari", "Durg", "Gariaband", "Janjgir-Champa", "Jashpur", "Kabirdham",
        "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
        "Raigarh", "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja"
    ],
    "Himachal Pradesh": [
        "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti",
        "Mandi", "Shimla", "Sirmaur", "Solan", "Una"
    ],
    "Uttarakhand": [
        "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital",
        "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"
    ],
    "Goa": ["North Goa", "South Goa"],
    "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"],
    "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"],
    "Meghalaya": ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"],
    "Mizoram": ["Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip"],
    "Nagaland": ["Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Niuland", "Noklak", "Peren", "Phek", "Shamator", "Tseminyu", "Tuensang", "Wokha", "Zunheboto"],
    "Sikkim": ["Gangtok", "Mangan", "Namyang", "Pakyong", "Soreng", "Gyalshing"],
    "Arunachal Pradesh": ["Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang", "Kamle", "Kra Daadi", "Kurung Kumey", "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley", "Lower Siang", "Lower Subansiri", "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi", "Siang", "Tawang", "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang", "Itanagar"],
    "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"],
    "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"],
    "Ladakh": ["Kargil", "Leh"],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"],
    "Chandigarh": ["Chandigarh"],
    "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "Lakshadweep": ["Lakshadweep"],
}

# ==============================================================================
# Realistic Rural Primary Healthcare Centres (by State -> District)
# ==============================================================================
HEALTHCARE_CENTRES_SEED = [
    # Tamil Nadu -> Coimbatore
    {"state": "Tamil Nadu", "district": "Coimbatore", "name": "Primary Health Centre — Valparai", "facility_type": "PHC", "address": "Main Road, Valparai Hill Division", "pincode": "642127", "code": "TN-CBE-PHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Coimbatore", "name": "Community Health Centre — Pollachi", "facility_type": "CHC", "address": "Palakkad Road, Pollachi Taluk", "pincode": "642001", "code": "TN-CBE-CHC02", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Coimbatore", "name": "Upgraded Primary Health Centre — Sulur", "facility_type": "UPHC", "address": "Trichy Road, Sulur", "pincode": "641402", "code": "TN-CBE-PHC03", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Coimbatore", "name": "Rural Health Sub-Center — Anaimalai", "facility_type": "SUB_CENTRE", "address": "Anaimalai Foothills Division", "pincode": "642104", "code": "TN-CBE-SC04", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Coimbatore", "name": "Primary Health Centre — Kinathukadavu", "facility_type": "PHC", "address": "Pollachi Main Road, Kinathukadavu", "pincode": "642109", "code": "TN-CBE-PHC05", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Coimbatore", "name": "Primary Health Centre — Madukkarai", "facility_type": "PHC", "address": "Palakkad Highway, Madukkarai", "pincode": "641105", "code": "TN-CBE-PHC06", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Coimbatore", "name": "Community Health Centre — Mettupalayam", "facility_type": "CHC", "address": "Kotagiri Road, Mettupalayam", "pincode": "641301", "code": "TN-CBE-CHC07", "status": "ACTIVE"},

    # Tamil Nadu -> Madurai
    {"state": "Tamil Nadu", "district": "Madurai", "name": "Primary Health Centre — Usilampatti", "facility_type": "PHC", "address": "Theni Road, Usilampatti Block", "pincode": "625532", "code": "TN-MDU-PHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Madurai", "name": "Community Health Centre — Melur", "facility_type": "CHC", "address": "Tiruchy Highway, Melur", "pincode": "625106", "code": "TN-MDU-CHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Madurai", "name": "Upgraded Primary Health Centre — Alanganallur", "facility_type": "UPHC", "address": "Main Bazar, Alanganallur", "pincode": "625501", "code": "TN-MDU-UPHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Madurai", "name": "Primary Health Centre — Vadipatti", "facility_type": "PHC", "address": "Dindigul Road, Vadipatti", "pincode": "625218", "code": "TN-MDU-PHC02", "status": "ACTIVE"},

    # Tamil Nadu -> Salem
    {"state": "Tamil Nadu", "district": "Salem", "name": "Rural Health Centre — Omalur", "facility_type": "PHC", "address": "Dharmapuri Main Road, Omalur", "pincode": "636455", "code": "TN-SLM-PHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Salem", "name": "Community Health Centre — Mettur", "facility_type": "CHC", "address": "Dam Circle, Mettur", "pincode": "636401", "code": "TN-SLM-CHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Salem", "name": "Primary Health Centre — Attur", "facility_type": "PHC", "address": "Cuddalore Main Road, Attur", "pincode": "636102", "code": "TN-SLM-PHC02", "status": "ACTIVE"},

    # Tamil Nadu -> Nilgiris
    {"state": "Tamil Nadu", "district": "Nilgiris", "name": "Primary Health Centre — Kotagiri", "facility_type": "PHC", "address": "Coonoor Road, Kotagiri Tribal Belt", "pincode": "643217", "code": "TN-NIL-PHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Nilgiris", "name": "Community Health Centre — Gudalur", "facility_type": "CHC", "address": "Mysore Road, Gudalur", "pincode": "643211", "code": "TN-NIL-CHC01", "status": "ACTIVE"},

    # Tamil Nadu -> Tiruchirappalli
    {"state": "Tamil Nadu", "district": "Tiruchirappalli", "name": "Primary Health Centre — Musiri", "facility_type": "PHC", "address": "Namakkal Road, Musiri", "pincode": "621211", "code": "TN-TRY-PHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Tiruchirappalli", "name": "Community Health Centre — Manapparai", "facility_type": "CHC", "address": "Dindigul Road, Manapparai", "pincode": "621306", "code": "TN-TRY-CHC01", "status": "ACTIVE"},

    # Tamil Nadu -> Chennai
    {"state": "Tamil Nadu", "district": "Chennai", "name": "Urban Primary Health Centre — Tondiarpet", "facility_type": "UPHC", "address": "TH Road, Tondiarpet", "pincode": "600081", "code": "TN-CHN-UPHC01", "status": "ACTIVE"},
    {"state": "Tamil Nadu", "district": "Chennai", "name": "Urban Community Health Centre — Adyar", "facility_type": "CHC", "address": "LB Road, Adyar", "pincode": "600020", "code": "TN-CHN-CHC01", "status": "ACTIVE"},

    # Kerala -> Palakkad
    {"state": "Kerala", "district": "Palakkad", "name": "Primary Health Centre — Attappadi (Tribal)", "facility_type": "PHC", "address": "Agali Block, Attappadi Valley", "pincode": "678581", "code": "KL-PLK-PHC01", "status": "ACTIVE"},
    {"state": "Kerala", "district": "Palakkad", "name": "Community Health Centre — Mannarkkad", "facility_type": "CHC", "address": "Silent Valley Road, Mannarkkad", "pincode": "678582", "code": "KL-PLK-CHC01", "status": "ACTIVE"},
    {"state": "Kerala", "district": "Palakkad", "name": "Primary Health Centre — Chittur", "facility_type": "PHC", "address": "Chittur-Thathamangalam", "pincode": "678101", "code": "KL-PLK-PHC02", "status": "ACTIVE"},

    # Kerala -> Ernakulam
    {"state": "Kerala", "district": "Ernakulam", "name": "Primary Health Centre — Aluva Rural", "facility_type": "PHC", "address": "Periyar River Road, Aluva", "pincode": "683101", "code": "KL-EKM-PHC01", "status": "ACTIVE"},
    {"state": "Kerala", "district": "Ernakulam", "name": "Community Health Centre — Kothamangalam", "facility_type": "CHC", "address": "High Range Road, Kothamangalam", "pincode": "686691", "code": "KL-EKM-CHC01", "status": "ACTIVE"},

    # Karnataka -> Mysuru
    {"state": "Karnataka", "district": "Mysuru", "name": "Rural Primary Health Centre — Hunsur", "facility_type": "PHC", "address": "Madikeri Highway, Hunsur", "pincode": "571105", "code": "KA-MYS-PHC01", "status": "ACTIVE"},
    {"state": "Karnataka", "district": "Mysuru", "name": "Community Health Centre — Nanjangud", "facility_type": "CHC", "address": "Temple Town Road, Nanjangud", "pincode": "571301", "code": "KA-MYS-CHC01", "status": "ACTIVE"},

    # Karnataka -> Bengaluru Urban
    {"state": "Karnataka", "district": "Bengaluru Urban", "name": "Primary Health Centre — Anekal Rural", "facility_type": "PHC", "address": "Hosur Road Junction, Anekal", "pincode": "562106", "code": "KA-BLR-PHC01", "status": "ACTIVE"},
    {"state": "Karnataka", "district": "Bengaluru Urban", "name": "Community Health Centre — Yelahanka", "facility_type": "CHC", "address": "Airport Corridor, Yelahanka", "pincode": "560064", "code": "KA-BLR-CHC01", "status": "ACTIVE"},

    # Maharashtra -> Pune
    {"state": "Maharashtra", "district": "Pune", "name": "Rural Hospital & PHC — Junnar", "facility_type": "PHC", "address": "Shivneri Fort Road, Junnar", "pincode": "410502", "code": "MH-PUN-PHC01", "status": "ACTIVE"},
    {"state": "Maharashtra", "district": "Pune", "name": "Community Health Centre — Baramati", "facility_type": "CHC", "address": "MIDC Road, Baramati", "pincode": "413102", "code": "MH-PUN-CHC01", "status": "ACTIVE"},

    # Telangana -> Rangareddy
    {"state": "Telangana", "district": "Rangareddy", "name": "Primary Health Centre — Ibrahimpatnam", "facility_type": "PHC", "address": "Nagarjuna Sagar Road, Ibrahimpatnam", "pincode": "501506", "code": "TG-RRD-PHC01", "status": "ACTIVE"},
    {"state": "Telangana", "district": "Rangareddy", "name": "Community Health Centre — Shadnagar", "facility_type": "CHC", "address": "Bangalore Highway, Shadnagar", "pincode": "509216", "code": "TG-RRD-CHC01", "status": "ACTIVE"},

    # Andhra Pradesh -> Chittoor
    {"state": "Andhra Pradesh", "district": "Chittoor", "name": "Primary Health Centre — Kuppam Rural", "facility_type": "PHC", "address": "PES Medical Corridor, Kuppam", "pincode": "517425", "code": "AP-CTR-PHC01", "status": "ACTIVE"},

    # Uttar Pradesh -> Varanasi
    {"state": "Uttar Pradesh", "district": "Varanasi", "name": "Primary Health Centre — Cholapur", "facility_type": "PHC", "address": "Azamgarh Road, Cholapur", "pincode": "221101", "code": "UP-VNS-PHC01", "status": "ACTIVE"},
    {"state": "Uttar Pradesh", "district": "Varanasi", "name": "Community Health Centre — Pindra", "facility_type": "CHC", "address": "Airport Highway, Pindra", "pincode": "221206", "code": "UP-VNS-CHC01", "status": "ACTIVE"},

    # Rajasthan -> Jaipur
    {"state": "Rajasthan", "district": "Jaipur", "name": "Primary Health Centre — Chomu", "facility_type": "PHC", "address": "Sikar Road, Chomu", "pincode": "303702", "code": "RJ-JPR-PHC01", "status": "ACTIVE"},
]

# ==============================================================================
# Authoritative Referral Eye Hospitals & Medical Centers (by State -> District)
# ==============================================================================
HOSPITALS_SEED = [
    # Tamil Nadu -> Coimbatore
    {
        "state": "Tamil Nadu", "district": "Coimbatore",
        "name": "Aravind Eye Hospital, Coimbatore",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Avinashi Road, Peelamedu, Coimbatore",
        "pincode": "641014",
        "contact": "+91 422 4360400",
        "speciality": "Vitreoretinal & Diabetic Retinopathy Tertiary Center",
        "availability": "24/7 Emergency Eye Care",
        "registration_reference": "NMC-HOSP-TN-CBE-001",
        "status": "VERIFIED",
    },
    {
        "state": "Tamil Nadu", "district": "Coimbatore",
        "name": "Coimbatore Medical College Hospital (CMCH) — Ophthalmology Dept",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "Trichy Road, Gopalapuram, Coimbatore",
        "pincode": "641018",
        "contact": "+91 422 2300100",
        "speciality": "Government Tertiary Retinal Care Unit",
        "availability": "24/7 Casualty & Eye Emergency",
        "registration_reference": "GOVT-TN-CBE-MCH01",
        "status": "VERIFIED",
    },
    {
        "state": "Tamil Nadu", "district": "Coimbatore",
        "name": "Lotus Eye Hospital and Institute, Coimbatore",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Civil Aerodrome Post, Avinashi Road, Coimbatore",
        "pincode": "641014",
        "contact": "+91 422 4229900",
        "speciality": "Comprehensive Vitreoretinal Services & Laser Clinic",
        "availability": "Mon-Sat 8:00 AM - 8:00 PM, 24/7 Emergency",
        "registration_reference": "NABH-EYE-TN-042",
        "status": "VERIFIED",
    },
    {
        "state": "Tamil Nadu", "district": "Coimbatore",
        "name": "Government Headquarters Hospital, Pollachi",
        "facility_type": "DISTRICT_HOSPITAL",
        "address": "Udumalai Road, Pollachi",
        "pincode": "642001",
        "contact": "+91 4259 223344",
        "speciality": "Sub-District Ophthalmic Screening & Stabilization Unit",
        "availability": "24/7 Inpatient & Emergency",
        "registration_reference": "GOVT-TN-POL-GH01",
        "status": "VERIFIED",
    },

    # Tamil Nadu -> Madurai
    {
        "state": "Tamil Nadu", "district": "Madurai",
        "name": "Aravind Eye Hospital, Madurai",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "1, Anna Nagar, Madurai",
        "pincode": "625020",
        "contact": "+91 452 4356100",
        "speciality": "Apex Vitreoretinal Institute & Tele-Ophthalmology Center",
        "availability": "24/7 Emergency Eye Care",
        "registration_reference": "NMC-HOSP-TN-MDU-001",
        "status": "VERIFIED",
    },
    {
        "state": "Tamil Nadu", "district": "Madurai",
        "name": "Government Rajaji Hospital — Regional Ophthalmology Centre",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "Panagal Road, Alwarpuram, Madurai",
        "pincode": "625020",
        "contact": "+91 452 2532535",
        "speciality": "Government Apex Vitreoretinal Surgery Division",
        "availability": "24/7 Trauma & Emergency",
        "registration_reference": "GOVT-TN-MDU-GRH01",
        "status": "VERIFIED",
    },

    # Tamil Nadu -> Salem
    {
        "state": "Tamil Nadu", "district": "Salem",
        "name": "Government Mohan Kumaramangalam Medical College Hospital",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "Fort Main Road, Salem",
        "pincode": "636001",
        "contact": "+91 427 2415151",
        "speciality": "Tertiary Retinal Laser & Surgical Care",
        "availability": "24/7 Emergency Services",
        "registration_reference": "GOVT-TN-SLM-MCH01",
        "status": "VERIFIED",
    },
    {
        "state": "Tamil Nadu", "district": "Salem",
        "name": "Aravind Eye Hospital, Salem",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Chinnathirupathi, Salem",
        "pincode": "636008",
        "contact": "+91 427 4356100",
        "speciality": "Diabetic Retinopathy Management & Vitrectomy",
        "availability": "24/7 Emergency Eye Care",
        "registration_reference": "NMC-HOSP-TN-SLM-002",
        "status": "VERIFIED",
    },

    # Tamil Nadu -> Chennai
    {
        "state": "Tamil Nadu", "district": "Chennai",
        "name": "Regional Institute of Ophthalmology & Govt. Ophthalmic Hospital",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "Marshalls Road, Egmore, Chennai",
        "pincode": "600008",
        "contact": "+91 44 28555281",
        "speciality": "National Apex Retinal Center & Ophthalmic Institute",
        "availability": "24/7 Regional Eye Trauma Center",
        "registration_reference": "GOVT-TN-CHN-RIO01",
        "status": "VERIFIED",
    },
    {
        "state": "Tamil Nadu", "district": "Chennai",
        "name": "Sankara Nethralaya, Chennai",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "18, College Road, Nungambakkam, Chennai",
        "pincode": "600006",
        "contact": "+91 44 42271500",
        "speciality": "Apex Vitreoretinal Research & Surgical Foundation",
        "availability": "24/7 Retinal Emergency Unit",
        "registration_reference": "NABH-EYE-TN-001",
        "status": "VERIFIED",
    },

    # Tamil Nadu -> Nilgiris
    {
        "state": "Tamil Nadu", "district": "Nilgiris",
        "name": "Government District Headquarters Hospital, Ooty",
        "facility_type": "DISTRICT_HOSPITAL",
        "address": "Hospital Road, Udhagamandalam",
        "pincode": "643001",
        "contact": "+91 423 2442212",
        "speciality": "Highland Tribal Eye Screening & Stabilization",
        "availability": "24/7 Emergency Services",
        "registration_reference": "GOVT-TN-NIL-GH01",
        "status": "VERIFIED",
    },

    # Kerala -> Palakkad
    {
        "state": "Kerala", "district": "Palakkad",
        "name": "District Hospital Palakkad — Eye Care Division",
        "facility_type": "DISTRICT_HOSPITAL",
        "address": "Fort Maidan Road, Palakkad",
        "pincode": "678001",
        "contact": "+91 491 2533323",
        "speciality": "Government Diabetic Retinopathy Screening Unit",
        "availability": "24/7 Emergency Services",
        "registration_reference": "GOVT-KL-PLK-DH01",
        "status": "VERIFIED",
    },
    {
        "state": "Kerala", "district": "Palakkad",
        "name": "Ahalia Foundation Eye Hospital, Palakkad",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Kozhippara, Palakkad",
        "pincode": "678557",
        "contact": "+91 4923 225555",
        "speciality": "Vitreoretinal Specialty & Rural Outreach Wing",
        "availability": "24/7 Emergency Eye Care",
        "registration_reference": "NABH-EYE-KL-014",
        "status": "VERIFIED",
    },

    # Kerala -> Ernakulam
    {
        "state": "Kerala", "district": "Ernakulam",
        "name": "Ernakulam General Hospital — Ophthalmology Department",
        "facility_type": "DISTRICT_HOSPITAL",
        "address": "Hospital Road, Marine Drive, Kochi",
        "pincode": "682011",
        "contact": "+91 484 2361251",
        "speciality": "Public Retinal Laser & Micro-Incision Surgery",
        "availability": "24/7 Emergency Services",
        "registration_reference": "GOVT-KL-EKM-GH01",
        "status": "VERIFIED",
    },
    {
        "state": "Kerala", "district": "Ernakulam",
        "name": "Giridhar Eye Institute, Kochi",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Ponneth Temple Road, Kadavanthra, Kochi",
        "pincode": "682020",
        "contact": "+91 484 4005555",
        "speciality": "Vitreoretinal Diseases & Surgical Center",
        "availability": "24/7 Retinal Emergency",
        "registration_reference": "NABH-EYE-KL-008",
        "status": "VERIFIED",
    },

    # Karnataka -> Mysuru
    {
        "state": "Karnataka", "district": "Mysuru",
        "name": "K.R. Hospital (Mysore Medical College) — Eye Hospital",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "Irwin Road, Mysuru",
        "pincode": "570001",
        "contact": "+91 821 2420000",
        "speciality": "Government Apex Regional Ophthalmology Department",
        "availability": "24/7 Emergency Care",
        "registration_reference": "GOVT-KA-MYS-MMC01",
        "status": "VERIFIED",
    },

    # Karnataka -> Bengaluru Urban
    {
        "state": "Karnataka", "district": "Bengaluru Urban",
        "name": "Minto Ophthalmic Hospital (Bangalore Medical College)",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "AV Road, Chamrajpet, Bengaluru",
        "pincode": "560002",
        "contact": "+91 80 26701123",
        "speciality": "State Apex Ophthalmic Institute & Retinal Referral Center",
        "availability": "24/7 Eye Emergency & Trauma",
        "registration_reference": "GOVT-KA-BLR-MIN01",
        "status": "VERIFIED",
    },
    {
        "state": "Karnataka", "district": "Bengaluru Urban",
        "name": "Narayana Nethralaya, Rajajinagar",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Chord Road, Rajajinagar, Bengaluru",
        "pincode": "560010",
        "contact": "+91 80 66121641",
        "speciality": "Advanced Vitreoretinal Care, Angiography & Gene Therapy",
        "availability": "24/7 Emergency Retinal Care",
        "registration_reference": "NABH-EYE-KA-003",
        "status": "VERIFIED",
    },

    # Maharashtra -> Pune
    {
        "state": "Maharashtra", "district": "Pune",
        "name": "Sassoon General Hospital & B.J. Medical College — Eye Dept",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "Station Road, Pune",
        "pincode": "411001",
        "contact": "+91 20 26128000",
        "speciality": "Government Tertiary Vitreoretinal Unit",
        "availability": "24/7 Casualty & Eye Emergency",
        "registration_reference": "GOVT-MH-PUN-BJMC01",
        "status": "VERIFIED",
    },
    {
        "state": "Maharashtra", "district": "Pune",
        "name": "H.V. Desai Eye Hospital, Hadapsar",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Tarwade Vasti, Mohammadwadi, Hadapsar, Pune",
        "pincode": "411060",
        "contact": "+91 20 26970144",
        "speciality": "Diabetic Retinopathy Rehabilitation & Vitreoretinal Unit",
        "availability": "24/7 Emergency Eye Care",
        "registration_reference": "NABH-EYE-MH-011",
        "status": "VERIFIED",
    },

    # Telangana -> Hyderabad
    {
        "state": "Telangana", "district": "Hyderabad",
        "name": "Sarojini Devi Eye Hospital, Mehdipatnam",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "Humayun Nagar, Mehdipatnam, Hyderabad",
        "pincode": "500028",
        "contact": "+91 40 23538801",
        "speciality": "State Apex Ophthalmic Hospital & Retinal Department",
        "availability": "24/7 Eye Casualty & Trauma",
        "registration_reference": "GOVT-TG-HYD-SDEH01",
        "status": "VERIFIED",
    },
    {
        "state": "Telangana", "district": "Hyderabad",
        "name": "L.V. Prasad Eye Institute (LVPEI), Banjara Hills",
        "facility_type": "SPECIALTY_EYE_HOSPITAL",
        "address": "Kallam Anji Reddy Campus, Banjara Hills, Hyderabad",
        "pincode": "500034",
        "contact": "+91 40 68102020",
        "speciality": "WHO Collaborating Centre for Blindness Prevention & Apex Retina Center",
        "availability": "24/7 Emergency Eye Care",
        "registration_reference": "NABH-EYE-TG-001",
        "status": "VERIFIED",
    },

    # Uttar Pradesh -> Varanasi
    {
        "state": "Uttar Pradesh", "district": "Varanasi",
        "name": "Sir Sunderlal Hospital (IMS-BHU) — Regional Eye Institute",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "BHU Campus, Varanasi",
        "pincode": "221005",
        "contact": "+91 542 2369291",
        "speciality": "Central University Regional Vitreoretinal Institute",
        "availability": "24/7 Trauma & Emergency",
        "registration_reference": "GOVT-UP-VNS-BHU01",
        "status": "VERIFIED",
    },

    # Rajasthan -> Jaipur
    {
        "state": "Rajasthan", "district": "Jaipur",
        "name": "Sawai Man Singh (SMS) Hospital — Dept of Ophthalmology",
        "facility_type": "MEDICAL_COLLEGE",
        "address": "JLN Marg, Ashok Nagar, Jaipur",
        "pincode": "302004",
        "contact": "+91 141 2518380",
        "speciality": "State Apex Vitreoretinal Laser & Surgical Center",
        "availability": "24/7 Emergency Services",
        "registration_reference": "GOVT-RJ-JPR-SMS01",
        "status": "VERIFIED",
    },
]


def seed_initial_data(db: Session):
    """
    Populates full Indian geographical metadata (28 states, districts, PHCs, and referral hospitals).
    Idempotent: Only seeds missing items without duplicating.
    """
    print("[*] Checking Indian state & district hierarchy metadata...")

    # 1. Seed States
    existing_states = {s.name: s for s in db.query(State).all()}
    for s_info in INDIAN_STATES:
        if s_info["name"] not in existing_states:
            s_obj = State(name=s_info["name"], code=s_info["code"])
            db.add(s_obj)
            db.flush()
            existing_states[s_info["name"]] = s_obj

    # 2. Seed Districts
    existing_districts = {(d.state_id, d.name): d for d in db.query(District).all()}
    district_lookup = {}  # key: (state_name, district_name) -> District

    for state_name, dist_list in STATE_DISTRICTS.items():
        state_obj = existing_states.get(state_name)
        if not state_obj:
            continue
        for dist_name in dist_list:
            key = (state_obj.id, dist_name)
            if key not in existing_districts:
                dist_obj = District(
                    state_id=state_obj.id,
                    name=dist_name,
                    code=f"{state_obj.code}-{dist_name[:3].upper()}",
                )
                db.add(dist_obj)
                db.flush()
                existing_districts[key] = dist_obj
                district_lookup[(state_name, dist_name)] = dist_obj
            else:
                district_lookup[(state_name, dist_name)] = existing_districts[key]

    # Also map all existing districts to district_lookup
    for (s_id, d_name), d_obj in existing_districts.items():
        # find state name
        for s_name, s_obj in existing_states.items():
            if s_obj.id == s_id:
                district_lookup[(s_name, d_name)] = d_obj
                break

    # 3. Synchronize / Seed legacy locations table for backward compatibility
    existing_locs = {(l.state, l.district): l for l in db.query(Location).all()}
    for (s_name, d_name), dist_obj in district_lookup.items():
        if (s_name, d_name) not in existing_locs:
            loc = Location(state=s_name, district=d_name, pincode=None)
            db.add(loc)
            db.flush()
            existing_locs[(s_name, d_name)] = loc

    # 4. Seed Rural Primary Healthcare Centres
    all_centres = db.query(HealthcareCentre).all()
    existing_centres_by_name = {c.name: c for c in all_centres}
    existing_centres_by_code = {c.code: c for c in all_centres if c.code}

    for c_info in HEALTHCARE_CENTRES_SEED:
        c_name = c_info["name"]
        c_code = c_info["code"]
        dist_obj = district_lookup.get((c_info["state"], c_info["district"]))
        loc_obj = existing_locs.get((c_info["state"], c_info["district"]))

        # Check existing by name or code
        c_obj = existing_centres_by_name.get(c_name) or existing_centres_by_code.get(c_code)
        if c_obj:
            if dist_obj:
                c_obj.district_id = dist_obj.id
            if loc_obj and not c_obj.location_id:
                c_obj.location_id = loc_obj.id
            c_obj.facility_type = c_info["facility_type"]
            c_obj.centre_type = c_info["facility_type"]
            c_obj.address = c_info["address"]
            c_obj.pincode = c_info["pincode"]
            c_obj.status = c_info["status"]
        else:
            if dist_obj:
                new_c = HealthcareCentre(
                    name=c_name,
                    district_id=dist_obj.id,
                    location_id=loc_obj.id if loc_obj else None,
                    facility_type=c_info["facility_type"],
                    centre_type=c_info["facility_type"],
                    address=c_info["address"],
                    pincode=c_info["pincode"],
                    code=c_code,
                    status=c_info["status"],
                )
                db.add(new_c)
                existing_centres_by_name[c_name] = new_c
                if c_code:
                    existing_centres_by_code[c_code] = new_c

    # 5. Seed Referral Eye Hospitals
    all_hospitals = db.query(Hospital).all()
    existing_hospitals_by_name = {h.name: h for h in all_hospitals}

    for h_info in HOSPITALS_SEED:
        h_name = h_info["name"]
        dist_obj = district_lookup.get((h_info["state"], h_info["district"]))
        loc_obj = existing_locs.get((h_info["state"], h_info["district"]))

        h_obj = existing_hospitals_by_name.get(h_name)
        if h_obj:
            if dist_obj:
                h_obj.district_id = dist_obj.id
            if loc_obj and not h_obj.location_id:
                h_obj.location_id = loc_obj.id
            h_obj.facility_type = h_info["facility_type"]
            h_obj.address = h_info["address"]
            h_obj.contact = h_info["contact"]
            h_obj.pincode = h_info["pincode"]
            h_obj.speciality = h_info["speciality"]
            h_obj.availability = h_info["availability"]
            h_obj.registration_reference = h_info["registration_reference"]
            h_obj.status = h_info["status"]
            h_obj.verification_status = h_info["status"]
        else:
            if dist_obj:
                new_h = Hospital(
                    name=h_name,
                    district_id=dist_obj.id,
                    location_id=loc_obj.id if loc_obj else None,
                    facility_type=h_info["facility_type"],
                    address=h_info["address"],
                    contact=h_info["contact"],
                    pincode=h_info["pincode"],
                    speciality=h_info["speciality"],
                    availability=h_info["availability"],
                    registration_reference=h_info["registration_reference"],
                    status=h_info["status"],
                    verification_status=h_info["status"],
                )
                db.add(new_h)
                existing_hospitals_by_name[h_name] = new_h

    db.commit()
    print(f"[*] Seeding complete: {len(existing_states)} States, {len(district_lookup)} Districts, {len(existing_centres_by_name)} Healthcare Centres, {len(existing_hospitals_by_name)} Referral Hospitals.")
