use anyhow::Result;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

const SAMPLE_RATE: u32 = 44100;
const DURATION_MS: u64 = 800;
const FREQUENCIES: &[f32] = &[2000.0, 4000.0];
const BIP_FREQ: f32 = 4000.0;

pub fn play_headphone_sequence() {
    let channels = &["left", "right", "both"];
    
    for &freq in FREQUENCIES {
        for &channel in channels {
            println!("Playing {} Hz on {} channel(s)", freq, channel);
            let _ = play_tone(freq, channel);
            thread::sleep(Duration::from_millis(DURATION_MS + 300));
        }
    }
}

pub fn play_speaker_sequence() {
    let channels = &["right", "left", "both"];
    
    for &freq in FREQUENCIES {
        for &channel in channels {
            println!("Playing {} Hz on {} speaker(s)", freq, channel);
            let _ = play_tone(freq, channel);
            thread::sleep(Duration::from_millis(DURATION_MS + 300));
        }
    }
}

pub fn test_microphone() -> Result<f32> {
    let host = cpal::default_host();
    let input_device = host.default_input_device()
        .ok_or_else(|| anyhow::anyhow!("No input device available"))?;

    let config = input_device.default_input_config()?;
    let sample_rate = config.sample_rate().0;
    
    // Play a tone
    let _ = play_tone(BIP_FREQ, "both");
    
    // Record for 1 second
    let samples = Arc::new(Mutex::new(Vec::new()));
    let samples_clone = samples.clone();
    
    let stream = input_device.build_input_stream(
        &config.into(),
        move |data: &[f32], _: &_| {
            let mut samples = samples_clone.lock().unwrap();
            samples.extend_from_slice(data);
        },
        |err| eprintln!("Error in stream: {}", err),
        None,
    )?;

    stream.play()?;
    thread::sleep(Duration::from_secs(1));
    drop(stream);

    // Calculate max amplitude
    let samples = samples.lock().unwrap();
    let max_amplitude = samples.iter().map(|s| s.abs()).fold(0.0f32, f32::max);

    Ok(max_amplitude)
}

fn play_tone(frequency: f32, channel: &str) -> Result<()> {
    let host = cpal::default_host();
    let device = host.default_output_device()
        .ok_or_else(|| anyhow::anyhow!("No output device available"))?;

    let config = device.default_output_config()?;
    let sample_rate = config.sample_rate().0 as f32;
    let channels = config.channels() as usize;

    let mut sample_clock = 0f32;
    let mut next_value = move || {
        sample_clock = (sample_clock + 1.0) % sample_rate;
        let value = (sample_clock * frequency * 2.0 * std::f32::consts::PI / sample_rate).sin();
        value * 0.5 // Volume at 50%
    };

    let stream = device.build_output_stream(
        &config.into(),
        move |data: &mut [f32], _: &_| {
            for frame in data.chunks_mut(channels) {
                let value = next_value();
                match channel {
                    "left" => {
                        frame[0] = value;
                        if frame.len() > 1 {
                            frame[1] = 0.0;
                        }
                    }
                    "right" => {
                        frame[0] = 0.0;
                        if frame.len() > 1 {
                            frame[1] = value;
                        }
                    }
                    _ => {
                        // both channels
                        for sample in frame.iter_mut() {
                            *sample = value;
                        }
                    }
                }
            }
        },
        |err| eprintln!("Error in stream: {}", err),
        None,
    )?;

    stream.play()?;
    thread::sleep(Duration::from_millis(DURATION_MS));
    drop(stream);

    Ok(())
}
