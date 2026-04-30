import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:get/get.dart';
import 'dart:math';

class OutPutPage extends StatelessWidget {
  const OutPutPage({super.key});

  @override
  Widget build(BuildContext context) {
    // ↓ 수정: Map으로 arguments 받기
    Map<String, dynamic> args = Get.arguments ?? {};
    List<String> urlList = List<String>.from(args["urls"] ?? []);
    List<String> coverList = List<String>.from(args["covers"] ?? []);
    String explanation = args["explanation"] ?? "";

    // ↓ 수정: randomUrl과 같은 인덱스의 커버 이미지 선택
    int randomIndex = urlList.isEmpty ? 0 : Random().nextInt(urlList.length);
    String randomUrl = urlList.isEmpty
      ? 'https://www.youtube.com/?bp=wgUCEAE%3D'
      : urlList[randomIndex];
    String coverUrl = coverList.isEmpty ? "" : coverList[randomIndex];

    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => Get.toNamed('/start'),
        child: const Icon(Icons.turn_left),
      ),

      // ↓ 수정: Stack → Column으로 변경, 설명·앨범커버·재생화면 순서로 배치
      body: Column(
        children: [
          // 설명 텍스트 박스
          if (explanation.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              color: Colors.black87,
              child: Text(
                explanation,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  height: 1.6,
                ),
              ),
            ),
          // 앨범 커버
          if (coverUrl.isNotEmpty)
            Image.network(
              coverUrl,
              width: double.infinity,
              height: 300,
              fit: BoxFit.cover,
            ),
          // 기존 Spotify 재생화면
          Expanded(
            child: InAppWebView(
              initialUrlRequest: URLRequest(url: WebUri(randomUrl)),
            ),
          ),
        ],
      )
    )
  }
}