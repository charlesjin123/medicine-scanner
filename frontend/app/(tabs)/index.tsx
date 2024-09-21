import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { useState, useRef, useEffect } from 'react';
import { Button, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import * as FileSystem from 'expo-file-system';
import axios from 'axios';
import apiKeyData from '../../google-api-key.json';

export default function HomeScreen() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const [ocrResult, setOcrResult] = useState('');
  const [apiKey, setApiKey] = useState('');
  const cameraRef = useRef(null);

  useEffect(() => {
    const loadApiKey = async () => {
      try {
        const apiKey = apiKeyData.api_key;
        setApiKey(apiKey);
      } catch (error) {
        console.error('Error reading API key file:', error);
      }
    };

    loadApiKey();
  }, []);

  if (!permission) {
    // Camera permissions are still loading.
    return <View />;
  }

  if (!permission.granted) {
    // Camera permissions are not granted yet.
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  const takePicture = async () => {
    console.log("taking picture");
    if (cameraRef.current) {
      const photo = await cameraRef.current.takePictureAsync({ base64: true });
      const fileUri = FileSystem.documentDirectory + 'photo.jpg';
      await FileSystem.writeAsStringAsync(fileUri, photo.base64, { encoding: FileSystem.EncodingType.Base64 });
      console.log("Photo saved to:", fileUri);
        const fileInfo = await FileSystem.getInfoAsync(fileUri);
        console.log("File info:", fileInfo);

        const ocrText = await performOcr(photo.base64);
      setOcrResult(ocrText);

    }
  };
  
  const performOcr = async (base64Image) => {
    try {
      const response = await axios.post(
        `https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`,
        {
          requests: [
            {
              image: {
                content: base64Image,
              },
              features: [
                {
                  type: 'TEXT_DETECTION',
                },
              ],
            },
          ],
        }
      );

      const textAnnotations = response.data.responses[0].textAnnotations;
      return textAnnotations.length > 0 ? textAnnotations[0].description : 'No text found';
    } catch (error) {
      console.error('Error performing OCR:', error);
      return 'Error performing OCR';
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
            <Text style={styles.text}>Take Picture of Medicine</Text>
          </TouchableOpacity>
        </View>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
  },
  camera: {
    flex: 1,
  },
  buttonContainer: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: 'transparent',
    margin: 64,
  },
  button: {
    flex: 1,
    alignSelf: 'flex-end',
    alignItems: 'center',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
});
