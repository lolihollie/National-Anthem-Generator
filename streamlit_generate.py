import streamlit as st
import pandas as pd
import numpy as np
import json
import random


st.markdown("""
<style>
hr.dotted {
    margin-top: 0px;
    margin-bottom: 0px;
    border-top: 1px dotted gray;
}
</style>
""", unsafe_allow_html=True)


if 'lyrics' not in st.session_state:
    st.session_state.lyrics = ""
if 'melody_ints' not in st.session_state:
    st.session_state.melody_ints = ""



def load_chain_from_json(file_path):
    with open(file_path, 'r') as json_file:
        chain_str_keys = json.load(json_file)
    chain = {eval(key): value for key, value in chain_str_keys.items()}
    return chain


def generate_lyrics(chain):
    words = [random.choice(chain[(None, "<START>")])]
    words.append(random.choice(chain[("<START>", words[-1])]))
    choice = ""
    while choice != "<END>" and len(words) < 100:
        choice = random.choice(chain[(words[-2], words[-1])])
        words.append(choice)
    lyrics = " ".join(words[:-1])
    return "\n".join(lyrics.split("<N>"))


def generate_melody(chain, start_bigram):
    # Initialize the melody with the start bigram
    melody = [start_bigram[0], start_bigram[1]]

    while True:
        current_bigram = (melody[-2], melody[-1])
        current_transitions = chain.get(current_bigram)
#        if not current_transitions:
#            break
        next_note = random.choice(current_transitions)
        if next_note == '<END>':
            break

        # Append the next note to the melody
        melody.append(next_note)

    # Return the generated melody, excluding the initial <START> and terminal <END> markers if present
    return melody[1:] if melody[-1] == '<END>' else melody




st.markdown('# Generate a National Anthem')
st.markdown('##### George Altshuler & Hollie Zheng')
st.markdown('<hr class="dotted"/>', unsafe_allow_html=True)


df = pd.read_csv('anthems.csv')

clusters = df['Cluster'].unique()  # Make sure 'df' is your DataFrame containing anthems
messages = {}
for cluster in ["God", "Monarchy", "Communism", "Patriotism", "War"]:  # Example clusters
    file_path = f'{cluster.lower()}.json'
    messages[cluster] = load_chain_from_json(file_path)

st.subheader('National Anthem Lyric Generator')

selected_cluster = st.radio("Select an Anthem 'Style' (cluster):", list(messages.keys()))

if st.button('Generate Anthem Lyrics'):
    # Generate lyrics and update the session state
    st.session_state.lyrics = generate_lyrics(messages[selected_cluster])

st.write(st.session_state.lyrics)


st.markdown('<hr class="dotted"/>', unsafe_allow_html=True)


st.subheader('National Anthem Melody Generator')

melody_chain = load_chain_from_json('all_melodies.json')

valid_start_bigrams = [k for k in melody_chain.keys() if isinstance(k, tuple) and k[0] == '<START>' and k[1] != '<END>']
start_bigram = random.choice(valid_start_bigrams)

melody = generate_melody(melody_chain, start_bigram)  # Pass the chain as an argument

melody_ints = [int(x) for x in melody[1:-1] if x != '<END>']
if st.button('Generate Anthem Melody'):
    melody = generate_melody(melody_chain, start_bigram)  # Generate melody
    melody = [int(x) for x in melody[1:-1] if x != '<END>']
    st.session_state.melody_ints = str(melody)

# Display the stored melody integers
st.write(st.session_state.melody_ints)

melody_str = ', '.join(map(str, melody))

# HTML content before the melody list
html_content_before = """
<html>
<head>
  <script type="module">
    import { Chuck } from 'https://cdn.jsdelivr.net/npm/webchuck/+esm';
    window.addEventListener('DOMContentLoaded', (event) => {
      document.getElementById('action').addEventListener('click', async () => {
        // Initialize default ChucK object, if not already initialized
        if (!window.theChuck) {
          window.theChuck = await Chuck.init([]);
        }
        // Run ChucK code
        window.theChuck.runCode(`
            ["""

# HTML content after the melody list
html_content_after = """] @=> int notes[];

            SinOsc osc => dac;

            0.5::second => dur noteDur;

            for(0 => int i; i < notes.size(); i++)
            {
                Std.mtof(notes[i]) => osc.freq;
                noteDur => now;
            }
            1::second => now;

        `);
      });
    });
  </script>
</head>
<body>
  <button id="action">Start and Play</button>
</body>
</html>

"""

# Combine the parts to form the final HTML content
html_content = html_content_before + melody_str + html_content_after

# Use the Streamlit components API to render the custom HTML
components.html(html_content, height=200)
