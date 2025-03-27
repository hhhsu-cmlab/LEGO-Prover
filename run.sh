python run_multiprocess.py \
  --data_split test \
  --ckpt_dir checkpoints/lego_prover_test/20250327_debug \
  --isabelle_path /home/hanyuan/Isabelle2022 \
  --model_name gpt-3.5-turbo \
  --num_prover 1 \
  --num_evolver 1 \
  --num_attempts 2
 