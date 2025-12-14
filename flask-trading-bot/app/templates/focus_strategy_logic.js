
// --- Lógica de Visualización de Estrategias ---
let globalStrategies = [];
let activePriceLines = [];

window.focusStrategy = function (index) {
    if (!candleSeries || !globalStrategies[index]) return;
    const strat = globalStrategies[index];

    // Limpiar líneas anteriores
    activePriceLines.forEach(line => candleSeries.removePriceLine(line));
    activePriceLines = [];

    const levels = strat.levels;

    // TARGET (Green)
    if (levels.target && !isNaN(parseFloat(levels.target))) {
        activePriceLines.push(candleSeries.createPriceLine({
            price: parseFloat(levels.target), color: '#10b981', lineWidth: 2, lineStyle: 0, title: `🎯 TARGET`, axisLabelVisible: true
        }));
    }
    // ENTRY (Blue)
    if (levels.entry && !isNaN(parseFloat(levels.entry))) {
        activePriceLines.push(candleSeries.createPriceLine({
            price: parseFloat(levels.entry), color: '#3b82f6', lineWidth: 2, lineStyle: 2, title: `🔵 ENTRY`, axisLabelVisible: true
        }));
    }
    // STOP (Red)
    if (levels.stop && !isNaN(parseFloat(levels.stop))) {
        activePriceLines.push(candleSeries.createPriceLine({
            price: parseFloat(levels.stop), color: '#ef4444', lineWidth: 2, lineStyle: 0, title: `🛑 STOP`, axisLabelVisible: true
        }));
    }

    console.log(`Visualizando niveles para: ${strat.name}`);
};
