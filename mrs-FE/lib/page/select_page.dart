import 'package:flutter/material.dart';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';
import 'package:get/get.dart' as getx;
import 'package:coco_music_app/page/output_page.dart';

class SelectPage extends StatelessWidget {
  SelectPage({super.key});
  final ImagePicker picker = ImagePicker();
  final getx.RxList<XFile> images = <XFile>[].obs; 
  late final XFile? image;
  final Dio dio = Dio();

  Future<void> uploadImages() async {
    List<MultipartFile> imageFiles = [];

    for (int i = 0; i < images.length; i++){
      var img = images[i];
      String filePath = img.path;
      String fileName = img.name;

      imageFiles.add(await MultipartFile.fromFile(filePath, filename: fileName));
    }
    String url = 'http://127.0.0.1:8000/api/upload';
    FormData formData = FormData.fromMap({
      'images': imageFiles,
    });

    try {
      Response response = await dio.post(url, data:formData);
      if(response.statusCode == 200) {
        List<String> urlList = List<String>.from(response.data["song_urls"]);
        List<String> coverList = List<String>.from(response.data["covers"]);  // ← 앨범커버 추가
        String explanation = response.data["explanation"] ?? "";
        print('success');
        getx.Get.to(() => const OutPutPage(), arguments: {
          "urls": urlList,
          "covers": coverList,
          "explanation": explanation
        });
      } else {
        print('image upload failed');
      }
    } catch (e) {
      print('Error uploading image: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    double screenHeight = MediaQuery.of(context).size.height;

    final uploadButton = Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          padding: const EdgeInsets.all(15),
          backgroundColor: Colors.purple,
        ),
        onPressed: () {
          uploadImages();
        },
        child: const Text("Upload", style: TextStyle(color: Colors.white))
      ),
    );

    return MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView( //스크롤이 가능한 UI
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(height: screenHeight * 0.13),
              _area(),
              uploadButton,
            ],
          ),
        ),
        floatingActionButton: Stack(
          children: [
            Align(      //카메라 버튼
              alignment: Alignment(Alignment.bottomRight.x, Alignment.bottomRight.y - 0.18),
              child: FloatingActionButton(
                onPressed: () async {
                  final image = await picker.pickImage(
                    source: ImageSource.camera,
                    maxHeight: 200,
                    maxWidth: 200,
                    imageQuality: 100
                  );
                  if(image != null) {
                    images.add(image);
                  }
                },
                heroTag: 'Image0',
                child: const Icon(Icons.camera),
              ),
            ),
            Align(      //앨범 버튼
              alignment: Alignment.bottomRight,
              child: FloatingActionButton(
                onPressed: () async {
                  final multiImage = await picker.pickMultiImage(
                    maxHeight: 200,
                    maxWidth: 200,
                    imageQuality: 100
                  );
                  images.addAll(multiImage);
                },
                heroTag: 'image1',
                child: const Icon(Icons.photo_album),
              ),
            )
          ],
        )
      )
    );
  }

  Widget _area() {
    return Container(
      margin: const EdgeInsets.all(10),
      child: getx.Obx(() => 
      GridView.builder(
        padding: const EdgeInsets.all(10),
        shrinkWrap: true,
        itemCount: images.length,
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3,
          childAspectRatio: 1/1,
          mainAxisSpacing: 10,
          crossAxisSpacing: 10
        ),
        itemBuilder: (BuildContext context, int index) {
          return Stack(
            alignment: Alignment.topRight,
            children: [
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(5),
                  image: DecorationImage(
                    fit: BoxFit.cover,
                    image: FileImage(File(images[index].path))
                  ),
                ),
              ),
              Container(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(5),
                ),
                child: IconButton(
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  icon: const Icon(Icons.close, color: Colors.white, size: 15,),
                  onPressed: (){
                    images.remove(images[index]);
                  },
                )
              )
            ],
          );
        },
      ),
      )
    );
  }
}