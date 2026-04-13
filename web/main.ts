type GroupName = "out" | "min";
type ChannelName = "r" | "g" | "b";

type SliderSet = {
  input: HTMLInputElement;
  valueText: HTMLSpanElement;
};

const defaultValues = {
  out: { r: 40, g: 40, b: 40 },
  min: { r: 125, g: 125, b: 125 },
};

const outputSlidersRoot = mustElement<HTMLDivElement>("outputSliders");
const minimumSlidersRoot = mustElement<HTMLDivElement>("minimumSliders");
const outputLock = mustElement<HTMLInputElement>("outputLock");
const minimumLock = mustElement<HTMLInputElement>("minimumLock");
const imageUpload = mustElement<HTMLInputElement>("imageUpload");
const previewCanvas = mustElement<HTMLCanvasElement>("previewCanvas");
const referenceImage = mustElement<HTMLImageElement>("referenceImage");
const saveBtn = mustElement<HTMLButtonElement>("saveBtn");
const resetBtn = mustElement<HTMLButtonElement>("resetBtn");
const pickColorBtn = mustElement<HTMLButtonElement>("pickColorBtn");
const statusText = mustElement<HTMLParagraphElement>("statusText");

const previewCtx = mustCanvasContext(previewCanvas);

const sliderMap: Record<string, SliderSet> = {};
let sourceImageData: ImageData | null = null;
let isSyncing = false;
let isPickColorMode = false;

buildSliderGroup("out", outputSlidersRoot);
buildSliderGroup("min", minimumSlidersRoot);

imageUpload.addEventListener("change", onImageUpload);
saveBtn.addEventListener("click", onSave);
resetBtn.addEventListener("click", onReset);
pickColorBtn.addEventListener("click", togglePickColorMode);
previewCanvas.addEventListener("click", onCanvasClick);
window.addEventListener("resize", updatePreview);

function mustElement<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing element: ${id}`);
  }
  return element as T;
}

function mustCanvasContext(canvas: HTMLCanvasElement): CanvasRenderingContext2D {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) {
    throw new Error("Canvas 2D context is not available.");
  }
  return ctx;
}

function buildSliderGroup(group: GroupName, root: HTMLElement): void {
  const channels: ChannelName[] = ["r", "g", "b"];

  for (const channel of channels) {
    const key = `${group}_${channel}`;
    const label = document.createElement("div");
    label.className = "channel";
    label.textContent = channel.toUpperCase();

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0";
    slider.max = "255";
    slider.value = String(defaultValues[group][channel]);

    const valueText = document.createElement("span");
    valueText.className = "value-pill";
    valueText.textContent = slider.value;

    slider.addEventListener("input", () => onSliderChange(group, channel, Number(slider.value)));

    root.append(label, slider, valueText);
    sliderMap[key] = { input: slider, valueText };
  }
}

function onSliderChange(group: GroupName, source: ChannelName, value: number): void {
  const changedKey = `${group}_${source}`;
  sliderMap[changedKey].valueText.textContent = String(value);

  if (isSyncing) {
    updatePreview();
    return;
  }

  const shouldLock = group === "out" ? outputLock.checked : minimumLock.checked;
  if (shouldLock) {
    syncTriplet(group, source, value);
  }

  updatePreview();
}

function syncTriplet(group: GroupName, source: ChannelName, value: number): void {
  isSyncing = true;
  const channels: ChannelName[] = ["r", "g", "b"];

  for (const channel of channels) {
    if (channel === source) {
      continue;
    }

    const key = `${group}_${channel}`;
    sliderMap[key].input.value = String(value);
    sliderMap[key].valueText.textContent = String(value);
  }

  isSyncing = false;
}

async function onImageUpload(): Promise<void> {
  const file = imageUpload.files?.[0];
  if (!file) {
    return;
  }

  const objectUrl = URL.createObjectURL(file);

  try {
    const img = await loadImage(objectUrl);
    drawSourceToCanvas(img);
    referenceImage.src = objectUrl;
    statusText.textContent = `Loaded ${file.name}`;
    setPickColorMode(false);
    updatePreview();
  } finally {
    setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
  }
}

function togglePickColorMode(): void {
  if (!sourceImageData) {
    statusText.textContent = "Upload an image before picking a color.";
    return;
  }

  setPickColorMode(!isPickColorMode);
  if (isPickColorMode) {
    statusText.textContent = "Click the preview image to sample a color.";
  }
}

function setPickColorMode(enabled: boolean): void {
  isPickColorMode = enabled;
  pickColorBtn.classList.toggle("is-active", enabled);
  previewCanvas.classList.toggle("picker-active", enabled);
}

function onCanvasClick(event: MouseEvent): void {
  if (!isPickColorMode || !sourceImageData) {
    return;
  }

  const rect = previewCanvas.getBoundingClientRect();
  const canvasX = Math.floor((event.clientX - rect.left) * (previewCanvas.width / rect.width));
  const canvasY = Math.floor((event.clientY - rect.top) * (previewCanvas.height / rect.height));

  const x = clamp(canvasX, 0, sourceImageData.width - 1);
  const y = clamp(canvasY, 0, sourceImageData.height - 1);
  const index = (y * sourceImageData.width + x) * 4;

  const red = sourceImageData.data[index];
  const green = sourceImageData.data[index + 1];
  const blue = sourceImageData.data[index + 2];

  setSliderValue("min_r", red);
  setSliderValue("min_g", green);
  setSliderValue("min_b", blue);

  setPickColorMode(false);
  statusText.textContent = `Sampled color R:${red} G:${green} B:${blue}`;
  updatePreview();
}

function setSliderValue(key: string, value: number): void {
  sliderMap[key].input.value = String(value);
  sliderMap[key].valueText.textContent = String(value);
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Failed to load image."));
    img.src = src;
  });
}

function drawSourceToCanvas(img: HTMLImageElement): void {
  const maxWidth = 1400;
  const maxHeight = 1000;
  const scale = Math.min(1, maxWidth / img.width, maxHeight / img.height);

  const targetWidth = Math.max(1, Math.round(img.width * scale));
  const targetHeight = Math.max(1, Math.round(img.height * scale));

  previewCanvas.width = targetWidth;
  previewCanvas.height = targetHeight;

  previewCtx.clearRect(0, 0, targetWidth, targetHeight);
  previewCtx.drawImage(img, 0, 0, targetWidth, targetHeight);
  sourceImageData = previewCtx.getImageData(0, 0, targetWidth, targetHeight);
}

function getSliderValue(group: GroupName, channel: ChannelName): number {
  return Number(sliderMap[`${group}_${channel}`].input.value);
}

function updatePreview(): void {
  if (!sourceImageData) {
    return;
  }

  const out = {
    r: getSliderValue("out", "r"),
    g: getSliderValue("out", "g"),
    b: getSliderValue("out", "b"),
  };

  const min = {
    r: getSliderValue("min", "r"),
    g: getSliderValue("min", "g"),
    b: getSliderValue("min", "b"),
  };

  const nextData = new Uint8ClampedArray(sourceImageData.data);

  for (let i = 0; i < nextData.length; i += 4) {
    const red = nextData[i];
    const green = nextData[i + 1];
    const blue = nextData[i + 2];

    if (red >= min.r && green >= min.g && blue >= min.b) {
      nextData[i] = out.r;
      nextData[i + 1] = out.g;
      nextData[i + 2] = out.b;
    }
  }

  const rendered = new ImageData(nextData, sourceImageData.width, sourceImageData.height);
  previewCtx.putImageData(rendered, 0, 0);
}

function onSave(): void {
  if (!sourceImageData) {
    statusText.textContent = "Upload an image before saving.";
    return;
  }

  previewCanvas.toBlob((blob) => {
    if (!blob) {
      statusText.textContent = "Save failed.";
      return;
    }

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "img_bright_recolored.png";
    link.click();
    URL.revokeObjectURL(url);
    statusText.textContent = "Saved img_bright_recolored.png";
  }, "image/png");
}

function onReset(): void {
  (Object.keys(sliderMap) as Array<keyof typeof sliderMap>).forEach((key) => {
    const [group, channel] = key.split("_") as [GroupName, ChannelName];
    const value = defaultValues[group][channel];
    sliderMap[key].input.value = String(value);
    sliderMap[key].valueText.textContent = String(value);
  });

  outputLock.checked = false;
  minimumLock.checked = false;
  setPickColorMode(false);
  updatePreview();
}
