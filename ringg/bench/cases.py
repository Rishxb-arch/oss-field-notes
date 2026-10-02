CLASSIFICATION = {
    "type": "object",
    "properties": {
        "call_outcome": {"type": "string", "enum": ["PROMISE_TO_PAY", "ALREADY_PAID", "REFUSED", "CALLBACK_REQUESTED", "WRONG_NUMBER", "NO_RESPONSE"]},
        "customer_sentiment": {"type": "string", "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE"]},
    },
    "required": ["call_outcome", "customer_sentiment"],
}
SCHEMA = {
    "type": "object",
    "properties": {
        "key_points": {"type": "array", "items": {"type": "string"}, "nullable": True},
        "action_items": {"type": "array", "items": {"type": "string"}, "nullable": True},
        "summary": {"type": "string"},
        "classification": CLASSIFICATION,
    },
    "required": ["summary", "classification"],
}
CASES = [
 ("ptp_hinglish", "PROMISE_TO_PAY",
  "Agent: Namaste, main XYZ Finance se Priya bol rahi hoon. Kya meri baat Rahul ji se ho rahi hai?\nCustomer: Haan bol raha hoon.\nAgent: Sir aapki EMI 4500 rupaye ki 5 tareekh ko due thi, abhi tak pending hai.\nCustomer: Haan madam, salary late aayi hai. Main 28 tareekh tak pakka kar dunga.\nAgent: Theek hai sir, 28 tak payment kar dijiye, main note kar leti hoon.\nCustomer: Ji thank you."),
 ("paid_devanagari", "ALREADY_PAID",
  "एजेंट: नमस्ते, मैं XYZ फाइनेंस से बोल रहा हूँ। आपकी EMI बाकी दिख रही है।\nग्राहक: भाई मैंने तो कल ही UPI से पेमेंट कर दिया था, स्क्रीनशॉट भी है।\nएजेंट: ठीक है सर, कृपया ट्रांजैक्शन ID बता दीजिए।\nग्राहक: T2409 से शुरू होता है, मैं व्हाट्सऐप पर भेज देता हूँ।\nएजेंट: धन्यवाद सर, हम चेक करके अपडेट कर देंगे।"),
 ("refused_english", "REFUSED",
  "Agent: Hi, this is Arjun from XYZ Finance regarding your overdue loan of 12,000 rupees.\nCustomer: I told you people last week, I am not paying. The product was defective and nobody helped me.\nAgent: Sir, the loan is separate from the product issue.\nCustomer: I don't care. Don't call me again.\nAgent: Understood sir, I will escalate your complaint."),
 ("callback_noisy_asr", "CALLBACK_REQUESTED",
  "Agent: hello namaste main xyz finance se\nCustomer: haan haan kaun [inaudible] abhi main gaadi chala raha hoon\nAgent: sir aapki emi ke baare mein\nCustomer: abhi baat nahi kar sakta shaam ko 6 baje call karo [noise]\nAgent: theek hai sir shaam 6 baje call karte hain"),
 ("wrong_number", "WRONG_NUMBER",
  "Agent: Hello, kya main Sunita Sharma ji se baat kar sakti hoon?\nCustomer: Nahi, yahan koi Sunita nahi hai. Aapne galat number lagaya hai.\nAgent: Sorry ma'am, yeh number humare records mein unke naam pe hai.\nCustomer: Mera number 3 saal se hai, koi Sunita nahi. Please record update kar lo."),
 ("empty", "NO_RESPONSE",
  "Agent: Hello? Hello? Kya aap sun pa rahe hain?\nAgent: Hello sir?\n[silence]\nAgent: Lagta hai call connect nahi hua, hum baad mein try karenge."),
]
