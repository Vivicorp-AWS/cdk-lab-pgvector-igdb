# [TODO] clone into ./tmp

REPO=sentence-transformers/all-MiniLM-L6-v2
MODEL_ID=all-MiniLM-L6-v2

echo "[INFO] Starting process"

echo "[INFO] Creating a asset directory (./assets)"
mkdir ./assets
cd ./assets

echo "[INFO] Part 1: Archive Model"

echo "[INFO] Cloning repo from https://huggingface.co/$REPO"
git clone https://huggingface.co/$REPO

echo "[INFO] Changing current directory to $MODEL_ID"
cd ./$MODEL_ID

echo "[INFO] Moving inference script"
cp -r ../../model/code ./

echo "[INFO] Packing model"
tar zcvf ./model.tar.gz *

echo "[INFO] Moving model archive to parent directory and removing repository directory"
mv ./model.tar.gz ../model.tar.gz
cd ..
rm -rf ./$MODEL_ID

echo "[INFO] Part 1 Finished. Browse ./asset/model.tar.gz to get the model archive"

echo "[INFO] Part 2: Download IGDB data files"

echo "[INFO] Cloning repo from https://github.com/VioletVivirand/igdb-data-examples"
git clone https://github.com/VioletVivirand/igdb-data-examples

echo "[INFO] Moving IGDB data files to parent directory, then remove the repository directory"
mv ./igdb-data-examples/*.csv ./igdb-data-examples/*.json ./
rm -rf ./igdb-data-examples

echo "[INFO] Part 2 Finished."

echo "[INFO] All Processes Finished."