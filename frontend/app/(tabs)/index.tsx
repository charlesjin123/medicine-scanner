import { CameraView, CameraType, useCameraPermissions } from "expo-camera";
import { useState, useRef, useEffect } from "react";
import { Button, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import * as FileSystem from "expo-file-system";
import axios from "axios";
import Ionicons from "@expo/vector-icons/Ionicons";

export default function HomeScreen() {
  const [facing, setFacing] = useState<CameraType>("back");
  const [permission, requestPermission] = useCameraPermissions();
  const [ocrResult, setOcrResult] = useState("");
  const cameraRef = useRef(null);

  if (!permission) {
    // Camera permissions are still loading.
    return <View />;
  }

  if (!permission.granted) {
    // Camera permissions are not granted yet.
    return (
      <View style={styles.container}>
        <Text style={styles.message}>
          We need your permission to show the camera
        </Text>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing((current) => (current === "back" ? "front" : "back"));
  }

  const takePicture = async () => {
    console.log("taking picture");
    if (cameraRef.current) {
      const photo = await cameraRef.current.takePictureAsync({ base64: true });

      // console.log(photo.uri);
      // console.log(photo.base64);

      try {
        const response = await axios.post(
          "http://10.102.93.8:5000/process_image",
          {
            base64: photo.base64,
          }
        );
        console.log("OCR Response:", response.data);
      } catch (error) {
        console.error("Error calling OCR API:", error);
      }
    }
  };

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} facing={facing} ref={cameraRef}>
        <View style={styles.buttonContainer}>
          {/* <TouchableOpacity style={styles.button} onPress={toggleCameraFacing}>
            <Text style={styles.text}>Flip Camera</Text>
          </TouchableOpacity> */}
          <TouchableOpacity style={styles.button} onPress={takePicture}>
            <Ionicons
              name="radio-button-on-sharp"
              size={85}
              color="hsl(180, 0%, 76%)"
            />
          </TouchableOpacity>
        </View>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
  },
  message: {
    textAlign: "center",
    paddingBottom: 10,
  },
  camera: {
    flex: 1,
  },
  buttonContainer: {
    flex: 1,
    flexDirection: "row",
    backgroundColor: "transparent",
    margin: 64,
  },
  button: {
    flex: 1,
    alignSelf: "flex-end",
    alignItems: "center",
  },
  text: {
    fontSize: 24,
    fontWeight: "bold",
    color: "white",
  },
});
