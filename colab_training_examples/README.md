# Google Colab Training Examples for GPT-ACT

This folder contains ready-to-use Google Colab notebooks for training ACT and SmolVLA policies on your recorded datasets.

## 📚 Available Notebooks

### ACT Training
- **`train_act_pick_and_place.ipynb`**: Train ACT policy for carrot pick-and-place task
  - Dataset: `so101-pick-and-place-carrot`
  - Training time: ~1.5 hours (100k steps on A100)

### SmolVLA Training
- **`train_smolvla_pick_and_place.ipynb`**: Train SmolVLA policy for carrot pick-and-place task
  - Dataset: `so101-pick-and-place-carrot`
  - Training time: ~5 hours (20k steps on A100)
  - ⚠️ Note: 20k steps is undertrained. For production, train 100k-200k steps.

## 🚀 How to Use

1. **Upload to Google Colab**
   - Go to [Google Colab](https://colab.research.google.com/)
   - Click `File` → `Upload notebook`
   - Select one of the `.ipynb` files from this folder

2. **Set GPU Runtime**
   - Click `Runtime` → `Change runtime type`
   - Set `Hardware accelerator` to `GPU` (preferably A100)

3. **Update Dataset and Model IDs**
   - Open the training cell (usually cell 10 or 11)
   - Update `--dataset.repo_id` to your HuggingFace dataset
   - Update `--policy.repo_id` to where you want the trained model uploaded

4. **Run All Cells**
   - Click `Runtime` → `Run all`
   - Log in to W&B and HuggingFace when prompted

5. **Monitor Training**
   - Check W&B dashboard for training progress
   - Checkpoints are saved to your Google Drive at `/content/drive/MyDrive/lerobot_runs/`

## 📖 Additional Resources

- [LeRobot Documentation](https://github.com/huggingface/lerobot)
- [HuggingFace Hub](https://huggingface.co/)
- [Weights & Biases](https://wandb.ai/)

## ⚠️ Important Notes

- **Google Drive Mount**: These notebooks save checkpoints to Google Drive to persist across sessions. Make sure you have enough space (~5-10GB per training run).
- **Session Timeout**: Free Colab sessions may disconnect after ~12 hours. Use Colab Pro for longer sessions.
- **Resume Training**: If disconnected, you can resume from the last checkpoint by updating the training command with `--resume=true` and `--checkpoint_path=/path/to/last/checkpoint`.

