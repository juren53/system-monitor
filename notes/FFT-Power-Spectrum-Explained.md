A **Power Spectrum** (calculated via FFT) is a tool used in signal processing to identify how much "energy" or "power" a signal has at different frequencies.

While a standard **FFT** (Fast Fourier Transform) gives you complex numbers (representing both magnitude and phase), the **Power Spectrum** simplifies this to show only the strength of the signal, discarding the phase information.

---

## 1. How it’s Calculated

To get the Power Spectrum from a time-domain signal, you follow these general steps:

1. **FFT:** Transform the signal from the time domain to the frequency domain using the FFT algorithm.
2. **Magnitude Squared:** Multiply each complex frequency component  by its complex conjugate .


3. **Scaling:** Depending on your needs, the result is often scaled by the number of samples  to represent the average power (often written as ).

---

## 2. Key Differences: FFT vs. Power Spectrum

| Feature | FFT | Power Spectrum |
| --- | --- | --- |
| **Output Type** | Complex Numbers (Real + Imaginary) | Real Numbers (Positive only) |
| **Information** | Magnitude and Phase | Magnitude (Power) only |
| **Use Case** | When you need to reconstruct the signal or know timing/phase. | When you only care about which frequencies are dominant. |
| **Units** | Linear (e.g., Volts) | Squared (e.g.,  or Watts) |

---

## 3. Power Spectrum vs. Power Spectral Density (PSD)

These terms are often used interchangeably, but they have a technical difference:

* **Power Spectrum:** Shows the power at specific discrete frequency bins. It is best for signals with clear, "pure" tones (sine waves).
* **Power Spectral Density (PSD):** Normalizes the power by the frequency resolution (bandwidth). It tells you how much power is in a 1 Hz wide band. It is the gold standard for analyzing **noise** or random signals where the energy is spread out.

---

## 4. Why use it?

* **Identifying Tones:** Finding a "hum" in an audio recording or a vibration in a piece of machinery.
* **Noise Analysis:** Measuring the "floor" of background noise in a communication system.
* **Data Compression:** Deciding which frequencies are important enough to keep and which can be discarded (e.g., in MP3 compression).

> **Note on "Leakage":** When calculating a Power Spectrum, engineers often use a **Window Function** (like Hann or Hamming) before the FFT. This prevents signal "leakage" where energy from one frequency spills into neighboring bins because the signal wasn't perfectly periodic within the sample window.

Would you like me to show you a simple Python or MATLAB code snippet to calculate and plot a power spectrum from a sample signal?
