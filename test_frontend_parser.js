
const parserTest = () => {
    // 1. Simulate the data structure
    const toolOutput = {
        "type": "line",
        "title": "Quarterly Revenue Growth",
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [
            {
                "label": "Revenue (M$)",
                "data": [12, 19, 15, 25]
            }
        ]
    };

    const aiText = `Here's a demo of a line chart showing quarterly revenue growth:

**Quarterly Revenue Growth**
*   **Q1:** 12 M$
*   **Q2:** 19 M$
*   **Q3:** 15 M$
*   **Q4:** 25 M$`;

    // 2. Simulate Backend Logic (appending JSON)
    const combinedResponse = aiText + "\n\n```json\n" + JSON.stringify(toolOutput, null, 2) + "\n```";

    console.log("--- Simulated Backend Response ---");
    console.log(combinedResponse);
    console.log("----------------------------------");

    // 3. Simulate Frontend Logic (ChatInterface.jsx)
    const isChart = (text) => {
        if (!text) return false;
        // Check for JSON-like structure (type, datasets) even if surrounded by text
        return text.includes('"type":') && text.includes('"datasets":') && text.includes('{');
    };

    const extractChartData = (data) => {
        try {
            // Extract JSON if embedded in text
            let jsonStr = data;
            const jsonMatch = data.match(/\{[\s\S]*"type"[\s\S]*"datasets"[\s\S]*\}/);
            if (jsonMatch) {
                jsonStr = jsonMatch[0];
            }

            // Clean markdown code blocks if present
            const cleanData = jsonStr.replace(/```json/g, '').replace(/```/g, '').trim();
            const chartData = JSON.parse(cleanData);
            return chartData;
        } catch (e) {
            return null;
        }
    };

    // 4. Run Verification
    console.log("\n--- Frontend Verification ---");
    const isChartDetected = isChart(combinedResponse);
    console.log(`isChart Detected: ${isChartDetected}`);

    if (isChartDetected) {
        const parsedData = extractChartData(combinedResponse);
        if (parsedData && parsedData.type === 'line' && parsedData.datasets.length > 0) {
            console.log("SUCCESS: Chart data extracted and parsed correctly!");
            console.log("Parsed Type:", parsedData.type);
            console.log("Parsed Title:", parsedData.title);
        } else {
            console.log("FAILURE: Parsing returned null or invalid data.");
        }
    } else {
        console.log("FAILURE: isChart returned false.");
    }
}

parserTest();
