package gnue.forms.components;


import javax.swing.*;
import java.awt.Frame;
import java.awt.Rectangle;
import java.awt.Dimension;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.List;
import java.util.ArrayList;

public class RegularDesktopComponent implements DesktopComponent {
	
	Rectangle lastFrameRect = new Rectangle(0, 0, 800, 600);
	static Dimension frameShowOffset  = new Dimension(30, 30);
	
	public FrameComponent[] getAllFrameComponents() {
		List<FrameComponent> fcs = new ArrayList<FrameComponent>();
		for (Frame f: Frame.getFrames()) {
			if (f instanceof FrameComponent) {
				fcs.add((FrameComponent)f);
			}
		}
		return (FrameComponent[])fcs.toArray(new FrameComponent[fcs.size()]);
	}
	
	public JComponent asComponent() {
		return null;
	}
	
	public FrameComponent createFrameComponent(String title, boolean resizable, boolean closable, boolean maximizable, boolean iconifiable, final Runnable onClose) {
		RegularFrameComponent frame = new RegularFrameComponent(title, resizable, closable, maximizable, iconifiable);
		
		frame.setVisible(true);

		// when user pressed close frame do nothing and send onClose to server
		frame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
		frame.addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent evt) {
				onClose.run();
			}
		});

		return frame;
	}
	
}

