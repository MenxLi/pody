npm run docs:build && 
rm -r pody/doc/* &&
touch pody/doc/.gitkeep &&
cp -r docs/.vitepress/dist/* pody/doc/