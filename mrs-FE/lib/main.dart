import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:coco_music_app/page/start_page.dart';
import 'package:coco_music_app/page/select_page.dart';

void main() {
  runApp(const HomePage());
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'Music App',
      //theme
      getPages: [
        GetPage(name: '/select', page: () => SelectPage()),
        GetPage(name: '/start', page: () => StartPage()),
      ],
      home: const StartPage()
    );
  }
}