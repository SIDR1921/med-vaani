from gtts import gTTS

# The ASHA Worker's Script (Single Patient)
text = """
Namaste. I am reporting a visit for patient Vikram Singh, age 42.
He has been complaining of high fever and severe joint pain for three days.
I checked his blood pressure, it is slightly low, 100 by 60.
Please advise on further treatment.
"""

print("Generating Single Patient English audio...")

# 'en' for English (with Indian accent simulation not possible directly in gTTS standard, 
# but 'en-in' tag works in some versions, sticking to 'en' for safety)
tts = gTTS(text=text, lang='en', slow=False)

# Save as .ogg
filename = "test_single_english.ogg"
tts.save(filename)

print(f"✅ Created {filename}")
print("👉 Drag and drop this file into your bot to test Single Entry!")