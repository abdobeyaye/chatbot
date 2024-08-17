import torch
from diffusers import FluxPipeline
from flask import Flask, request, jsonify, send_file, render_template
from io import BytesIO

app = Flask(__name__)

# تحميل النموذج
pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev", torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'لم يتم توفير نص وصفي'}), 400
    
    try:
        # توليد الصورة
        image = pipe(
            prompt,
            height=512,
            width=512,
            guidance_scale=3.5,
            num_inference_steps=30,
            max_sequence_length=512,
            generator=torch.Generator("cpu").manual_seed(0)
        ).images[0]
        
        # تحويل الصورة إلى بايتات
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
